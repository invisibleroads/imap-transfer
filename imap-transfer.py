'Command-line script to duplicate emails from one IMAP server to another'
import re
import os
import sys
import socket
import logging
import datetime
from argparse import ArgumentParser
from calendar import timegm
from ConfigParser import ConfigParser, NoSectionError, NoOptionError
from email.utils import mktime_tz, parseaddr, parsedate_tz
from formencode import Invalid, Schema, validators
from imapIO import IMAP4, IMAP4_SSL, IMAPError, normalize_folder
from sqlalchemy import Column, Date, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


DESCRIPTION = 'Revive messages from source mailbox to target mailbox'
SOCKET = socket.socket()
PATTERN_PORT = re.compile(r'(\d+)')
RAW_FROM_LEN_MAX = 32
RAW_DATE_LEN_MAX = 32
SESSION = sessionmaker()
DB = SESSION()
BASE = declarative_base()
BASE_PATH = os.path.dirname(__file__)
EXPAND_PATH = lambda x: os.path.join(BASE_PATH, x)
SCRIPT_NAME = os.path.splitext(os.path.basename(__file__))[0]


class Application(object):

    def __init__(self):
        self.args = parse_args()
        if self.args.verbose:
            log = logging.getLogger('imapIO')
            log.addHandler(logging.StreamHandler())
        self.load_configuration()
        self.lock_port()
        self.connect()

    def load_configuration(self):
        self.configParser = ConfigParser()
        configurationPath = self.args.configurationPath
        try:
            self.configParser.read(configurationPath)
            self.configParser.read('.' + configurationPath)
        except Exception, error:
            print 'Could not parse %s' % configurationPath
            print error
            sys.exit(1)

    def lock_port(self):
        'Make sure only one instance of this script is running'
        section, portlock = 'app:portlock', 'imap-transfer'
        try:
            portString = self.configParser.get(section, portlock)
        except (NoSectionError, NoOptionError):
            print ('To ensure that only one instance of this script is running, '
                    "specify a unique port number for '%s' in '%s'" % (portlock, section))
        else:
            port = parse_port(portString)
            try:
                SOCKET.bind(('', port))
            except socket.error:
                sys.exit(1)

    def connect(self):
        'Connect to IMAP servers and database'
        try:
            sourceParameterByKey = load_parameterByKey('source', self.configParser)
            targetParameterByKey = load_parameterByKey('target', self.configParser)
        except ApplicationError, error:
            print error
            sys.exit(1)
        try:
            self.send_feedback('[%(host)s] Connecting to source: %(username)s' % sourceParameterByKey)
            self.sourceServer = connect(sourceParameterByKey)
            self.send_feedback('[%(host)s] Connecting to target: %(username)s' % targetParameterByKey)
            self.targetServer = connect(targetParameterByKey)
        except IMAPError, error:
            print error
            sys.exit(1)
        # Prepare database
        engine = create_engine('sqlite:///%s-%s.db' % (
            '%(username)s' % sourceParameterByKey,
            '%(username)s' % targetParameterByKey))
        DB.configure(bind=engine)
        BASE.metadata.bind = engine
        BASE.metadata.create_all(engine)

    def revive_messages(self):
        'Revive sourceServer messages in targetServer'
        # Get most recent scan date
        searchCriterion = ''
        if self.args.incremental:
            result = DB.query(Message.date).order_by(Message.date.desc()).first()
            if result:
                searchCriterion = 'SINCE %s' % result[0].strftime('%d-%b-%Y')
                self.send_feedback(searchCriterion)
        reviveCount = 0
        # Walk sourceServer
        for email in self.sourceServer.walk(searchCriterion=searchCriterion):
            # If we already have a record of this email,
            if has_record(email):
                continue
            # If the message does not exist in the target mailbox,
            if not has(self.targetServer, email):
                self.send_feedback(email['subject'].encode('utf-8'))
                # Revive message in target mailbox
                self.targetServer.revive(email.folder, email)
                # Record email in our local database
                record(email)
                # Track reviveCount
                reviveCount += 1
                if reviveCount >= self.args.maximumReviveCount:
                    self.send_feedback('Reached maximumReviveCount=%s' % reviveCount)
                    break

    def send_feedback(self, feedback):
        if self.args.verbose:
            print feedback


class ApplicationError(Exception):
    pass


class Message(BASE):
    __tablename__ = 'messages'
    id = Column(Integer, primary_key=True)
    raw_from = Column(String(RAW_FROM_LEN_MAX))
    raw_date = Column(String(RAW_DATE_LEN_MAX))
    date = Column(Date)


class IMAPForm(Schema):

    host = validators.String
    port = validators.Int
    username = validators.String
    password = validators.String
    ssl = validators.StringBool


def parse_args():
    argumentParser = ArgumentParser(description=DESCRIPTION)
    argumentParser.add_argument('-c',
        default=EXPAND_PATH(SCRIPT_NAME) + '.ini',
        dest='configurationPath',
        help='use the specified configuration file',
        metavar='PATH')
    argumentParser.add_argument('-n',
        default=None,
        dest='maximumReviveCount',
        help='limit the maximum number of messages revived',
        metavar='N',
        type=int)
    argumentParser.add_argument('-q',
        action='store_false',
        default=True,
        dest='verbose',
        help='be quiet')
    argumentParser.add_argument('-i',
        action='store_true',
        default=False,
        dest='incremental',
        help='since last recorded date (fast but may skip messages)')
    return argumentParser.parse_args()


def parse_port(portString):
    'Convert string to integer while ignoring other text such as comments'
    match = PATTERN_PORT.search(portString)
    try:
        return int(match.group(1))
    except AttributeError:
        raise ValueError('Could not parse port=%s' % portString)


def parse_whenLocal(message):
    timePack = parsedate_tz(message['date'])
    if not timePack:
        return
    timeStamp = timegm(timePack) if timePack[-1] is None else mktime_tz(timePack)
    return datetime.datetime.fromtimestamp(timeStamp)


def load_parameterByKey(section, configParser):
    try:
        parameterByKey = dict(configParser.items(section))
    except NoSectionError:
        raise ApplicationError('Configuration is missing section: %s' % section)
    try:
        parameterByKey = IMAPForm().to_python(parameterByKey)
    except Invalid, error:
        lines = ['Error parsing section: %s' % section]
        for key, value in error.unpack_errors().iteritems():
            lines.append('%s: %s' % (key, value))
        raise ApplicationError('\n'.join(lines))
    return parameterByKey


def connect(parameterByKey):
    IMAPClass = IMAP4_SSL if parameterByKey['ssl'] else IMAP4
    return IMAPClass.connect(
        parameterByKey['host'],
        parameterByKey['port'],
        parameterByKey['username'],
        parameterByKey['password'])


def has(server, message):
    'Return True if the IMAP server has a copy of the message'
    messageFrom = message['fromWhom']
    messageDate = message['date']
    whenLocal = parse_whenLocal(message)
    # Without a date, I cannot easily test for duplicates
    if not whenLocal:
        return False
    include = lambda _: not normalize_folder(_).startswith('[gmail]')  # Exclude virtual folders
    searchCriterion = 'FROM "%s" SENTON "%s"' % (parseaddr(messageFrom)[1], whenLocal.strftime('%d-%b-%Y'))
    messageGenerator = server.walk(include, searchCriterion=searchCriterion)
    for m in messageGenerator:
        if m['date'] == messageDate:
            return True
    return False


def has_record(message):
    'Return True if we have already have a record of this message'
    result = DB.query(Message.id).filter(
        (Message.raw_from==message['fromWhom'][:RAW_FROM_LEN_MAX]) &
        (Message.raw_date==message['date'][:RAW_DATE_LEN_MAX])).first()
    return True if result else False


def record(message):
    'Record the message in our database'
    DB.add(Message(
        raw_from=message['fromWhom'][:RAW_FROM_LEN_MAX],
        raw_date=message['date'][:RAW_DATE_LEN_MAX],
        date=parse_whenLocal(message).date()))
    DB.commit()


if '__main__' == __name__:
    app = Application()
    app.revive_messages()
