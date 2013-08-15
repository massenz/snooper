=========================
Deploy Snooper to RM Prod
=========================


To access the Prod postgresql::

    psql -d dencloud -U rmview -h 10.10.122.120

Install gcc, Python 2.7 and easy_install::

    sudo bash
    yum install rmpython27.x86_64
    yum install rmpython27-setuptools
    yum install gcc

Install virtualenv, create an env and activate it::

    sudo easy_install-2.7 virtualenv
    virtualenv -p `which python2.7` $HOME/env/snooper
    source ~/env/snooper/bin/activate

To install the postgres Python library, ``pg_config`` tool must be in the ``PATH``::

    export PATH=/usr/pgsql-9.2/bin:$PATH

Installing snooper, will bring in all deps in the virtualenv::

    easy_install snooper-0.11-py2.7.egg 

at this point gcc can be removed, no longer necessary.

Try that you can run a query::

    snooper --conf snooper/snooper.conf --host 10.10.122.120 --env prod "SELECT name FROM CLOUD_TARGETS"

Launch the web server, this will be reachable at: http://10.10.20.180:5000
::

    snooper-webui --conf snooper/snooper.conf --queries snooper/queries.json --env prod --host 10.10.122.120 --debug

To test that coupons can be created, use snooper CLI, or just run the test script (``test-snooper.sh ``)::

    #!/bin/bash

    echo 'Running a test of Snooper'

    HOST='10.10.122.120'
    FILE='coupons.txt'
    NUM=3
    CONF="$HOME/snooper/snooper.conf"

    if [ ! -e $CONF ]; then
       echo "No configuration file $CONF found, please create one before running this test"
       exit 1
    fi

    snooper --coupons=$NUM --cloud="Peak CoLo" \
        --provider=RM-Internal --out=$FILE --conf=$CONF \
        --env=prod --host=$HOST

    if [ $? != 0 ]; then
        echo '[ERROR] could not create coupons'
        exit 1
    fi

    echo "$NUM Promotion Codes saved in $FILE"
    cat $FILE

    echo 'done'

Sample run::

    $ ./test-snooper.sh 
    
    Running a test of Snooper
    Generating 3 Promotion Codes
    Found Service Provider RM-Internal [f374275f-52d3-47ef-97f1-01ed2daa20cd]
    Found Cloud Target Peak CoLo [0691114f-fa46-4e4c-9f37-18e91679b948]: https://vcd.peakcolo.com
    Done - generated 3 coupons
    Saved the list of codes to coupons.txt
    3 Promotion Codes saved in coupons.txt
    # RiverMeadow Software, Inc. - created 2013-08-14T22:32:32.775715
    #
    # For Service Provider: RM-Internal [f374275f-52d3-47ef-97f1-01ed2daa20cd]
    # Cloud Target: Peak CoLo [0691114f-fa46-4e4c-9f37-18e91679b948] https://vcd.peakcolo.com
    # This file contains 3 promotion codes

    R4E7-456A-YLUJ
    W474-TJE1-E9FR
    OVJ2-UCM4-AYOI
    done

