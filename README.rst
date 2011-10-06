imap-transfer
=============
Here is a simple command-line script to duplicate emails from one IMAP server to another.  The script has been tested using Lotus Domino as an IMAP source and Gmail as an IMAP target.


Installation
------------
::

    IMAP_TRANSFER_ENV=$HOME/Projects/imap-transfer-env
    mkdir -p $IMAP_TRANSFER_ENV

    # Prepare
    virtualenv --no-site-packages $IMAP_TRANSFER_ENV
    source $IMAP_TRANSFER_ENV/bin/activate
    pip install formencode imapIO sqlalchemy

    # Download
    git clone git://github.com/invisibleroads/imap-transfer.git $IMAP_TRANSFER_ENV/app

    # Configure
    cd $IMAP_TRANSFER_ENV/app
    cp imap-transfer.ini .imap-transfer.ini
    vim .imap-transfer.ini


Usage
-----
::

    source $IMAP_TRANSFER_ENV/bin/activate
    cd $IMAP_TRANSFER_ENV/app
    python imap-transfer.py --help


Crontab
-------
::

    # Revive 100 random messages incrementally since last scan date
    5-59/15 8-20 * * * IMAP_TRANSFER_ENV=$HOME/Projects/imap-transfer-env; source $IMAP_TRANSFER_ENV/bin/activate; cd $IMAP_TRANSFER_ENV/app; python imap-transfer.py -n 100 >> imap-transfer.log 2>&1
    # Revive 100 random messages from entire mailbox
    0 0-7,21-23 * * * IMAP_TRANSFER_ENV=$HOME/Projects/imap-transfer-env; source $IMAP_TRANSFER_ENV/bin/activate; cd $IMAP_TRANSFER_ENV/app; python imap-transfer.py -n 100 -f >> imap-transfer.log 2>&1
