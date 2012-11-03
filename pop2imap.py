from email import message_from_string
from imapIO import IMAP4_SSL
from poplib import POP3_SSL


SOURCE_USERNAME = 'user@hotmail.com'
SOURCE_PASSWORD = 'password'
TARGET_USERNAME = 'user@gmail.com'
TARGET_PASSWORD = 'password'


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
print 'Counting messages on POP3...'
messageCount = len(sourceServer.list()[1])
for messageIndex in xrange(1, 1 + messageCount):
    print 'Reviving %s / %s' % (messageIndex, messageCount)
    message = message_from_string('\r\n'.join(sourceServer.retr(messageIndex)[1]))
    message['date'] = message['Date']
    targetServer.revive('Inbox', message)
