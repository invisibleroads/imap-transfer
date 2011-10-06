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

    5-59/15 * * * * IMAP_TRANSFER_ENV=$HOME/Projects/imap-transfer-env; source $IMAP_TRANSFER_ENV/bin/activate; cd $IMAP_TRANSFER_ENV/app; python imap-transfer.py -n 100 >> imap-transfer.log 2>&1
