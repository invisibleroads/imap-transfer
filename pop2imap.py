import os
from email import message_from_string
from imapIO import IMAP4_SSL
from poplib import POP3_SSL
from socket import socket


SOCKET = socket()
PORT = 9000
SOURCE_USERNAME = 'username@hotmail.com'
SOURCE_PASSWORD = 'password'
TARGET_USERNAME = 'username@gmail.com'
TARGET_PASSWORD = 'password'


def run():
    try:
        SOCKET.bind(('', PORT))
    except socket.error:
        return
    print 'Connecting to POP3...'
    sourceServer = POP3_SSL('pop3.live.com')
    sourceServer.user(SOURCE_USERNAME)
    sourceServer.pass_(SOURCE_PASSWORD)
    print 'Connecting to IMAP4...'
    targetServer = IMAP4_SSL.connect(
        'imap.gmail.com',
        993,
        TARGET_USERNAME,
        TARGET_PASSWORD)
    print 'Counting messages on IMAP4...'
    messageCount = len(sourceServer.list()[1])
    messagePath = os.path.splitext(__file__)[0] + '.txt'
    try:
        messageIndexStart = int(open(messagePath).read()) + 1
    except IOError:
        messageIndexStart = 1
    if messageIndexStart > messageCount:
        return
    for messageIndex in xrange(messageIndexStart, messageCount + 1):
        print 'Reviving %s / %s' % (messageIndex, messageCount)
        message = message_from_string('\r\n'.join(sourceServer.retr(messageIndex)[1]))
        message['date'] = message['Date']
        targetServer.revive('Inbox', message)
        open(messagePath, 'wt').write(str(messageIndex))


if __name__ == '__main__':
    run()
