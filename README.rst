imap-transfer
=============
Here is a simple command-line script to duplicate emails from one IMAP server to another.  The script has been tested using Lotus Domino as an IMAP source and Gmail as an IMAP target.


Installation
------------
::

    IMAP_TRANSFER_ENV=imap-transfer-env
    virtualenv --no-site-packages $IMAP_TRANSFER_ENV
    source $IMAP_TRANSFER_ENV/bin/activate
    pip install formencode imapIO sqlalchemy
    cp imap-transfer.ini .imap-transfer.ini
    vim .imap-transfer.ini


Usage
-----
::

    source $IMAP_TRANSFER_ENV/bin/activate
    python imap-transfer.py --help
