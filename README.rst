========================================
Snooper - a DB query execution framework
========================================

:Date: 2013-07-11
:Author: M. Massenzio
:Version: 0.3
:Updated: 2013-10-03

Use Case
--------

This allows one to explore (or modify) the state of some of the Tables in the Postgres DB
by running an arbitrary query against a dev (or Prod) instance.

There may also be a set of predefined queries that may be run automatically; further, these
predefined queries may have a number of parameters that will have to be substituted before
executing them.

The output of the script must be suitable for both human and machine (eg, piping) consumption

Implementation
--------------

This is a python script that takes a number of command-line arguments, constructs the query and
then executes it against a specified VM instance.

The output format will initially be JSON, but it will eventually be possible for the user to choose
from a predefined set (eg, CSV, HTML table, etc.)

Command-line arguments
^^^^^^^^^^^^^^^^^^^^^^

These can be seen using the ``--help`` option::

    $ python snooper.py --help
    usage: snooper.py [-h] [--queries QUERIES] [--out OUT] [--host HOST]
                      [--format FORMAT] [--query QUERY] [--list] [--env ENV]
                      [--debug] --conf CONF [--coupons COUPONS]
                      [--provider PROVIDER] [--cloud CLOUD]
                      [param [param ...]]

    SQL command line execution tool

    positional arguments:
      param                 positional parameters for the query

    optional arguments:
      -h, --help            show this help message and exit
      --queries QUERIES     an optional input file (JSON) defining a set of SQL
                            queries
      --out FILE            an optional output file
      --host HOST           the host to run the query against (must be running the
                            Postgres server and have the external port accessible
      --format FORMAT       the format for the output
      --query QUERY, -q QUERY
                            used in conjunction with --queries, specifies the
                            named query to run
      --list, -l            Lists all available queries in the files specified
                            with the --queries flag and exits
      --env ENV             the section in the {'const': None, 'help': 'the
                            section in the %s configuration file, from which to
                            take the connection configuration parameters',
                            'option_strings': ['--env'], 'dest': 'env',
                            'required': False, 'nargs': None, 'choices': None,
                            'default': 'dev', 'prog': 'snooper.py', 'container':
                            <argparse._ArgumentGroup object at 0x106e7ced0>,
                            'type': None, 'metavar': None} configuration file,
                            from which to take the connection configuration
                            parameters
      --debug               If set, the server will be run in debug mode: do NOT
                            use in production
      --conf CONF           The location of the configuration file which contains
                            the connection parameters
      --coupons COUPONS     This will generate the requested number of coupons,
                            insert in the database and return in the --out file
                            the list of codes. MUST specify --provider and --cloud
                            UUIDs
      --provider PROVIDER   The name of the Service Provider for the coupons
      --cloud CLOUD         The name of the Cloud Target for the promotion codes



If the query to run has named arguments, then those should be passed in (for now, I will only
support `positional` arguments).

For example, say you want to run the ``get_user`` query from the ``queries.json`` file::

    "queries": {
        "get_user_by_id": {
            "sql": "SELECT username, first_name, last_name FROM USER WHERE ID=%(id)s",
            "drill_down": {
                "username": "/api/1/query/get_user_by_username/username/$"
            }
        },
        ...
    }

then one would invoke the script as follows::

    snooper --queries queries.json --host 10.10.121.99 --query get_user id 99

the script would then run the query as follows::

    SELECT USERNAME, PASSWORD FROM USER WHERE ID=99

The *(name, value)* pair must always be passed like shown above (with a space, **no** ``=``):
this would be an error::

    snooper --queries queries.json --host 10.10.121.99 --query get_user id=99  # WRONG


Alternatively, the script can be used to run an arbitrary SQL query from the command line::

    snooper --host 10.10.121.99 'SELECT USERNAME, PASSWORD FROM USER WHERE ID=99'

Please note it's an **error** to pass both the ``--queries`` argument and a query (in this case,
the query literal would be incorrectly interpreted as one of the query's positional parameters).

Promotion Codes
+++++++++++++++

**Snooper** can be used to create `Promotion Codes`_ too: please see the documentation_

.. _Promotion Codes: https://github.com/RiverMeadow/encloud/blob/develop/docs/coupons.rst
.. _documentation: https://github.com/massenz/snooper/blob/develop/promotion_codes.rst

Connection parameters
^^^^^^^^^^^^^^^^^^^^^

These are taken from a configuration file (defined by the ``--conf`` option) and grouped
by *environments*, as in::

    # Connection configuration for Snooper

    [dev]
    db = mydb
    user = uzer
    password = duba
    host = 10.10.121.99

    [prod]
    db = pencloud
    user = zooz
    password = blaaaz

Use the ``--env`` command-line arg to specify a given environment (``dev`` is used by default).

**Note** the ``hostname`` **can** be specified via the configuration file, or via the ``--host``
command-line argument (if specified in both, CLI option takes precedence).

Drill down
^^^^^^^^^^

This is mostly useful for UI clients taking advantage of the `REST API`_, and allows one to
execute a chain of *drill-down* queries.

Taking as an example this query::

    "queries": {
        "get_user_by_role": {
            "sql": "SELECT uuid,email_address,first_name,last_name FROM users WHERE role=%(uuid)s",
            "drill_down": {
                "uuid": "/api/1/query/get_user_by_id/id/$"
            }
        }
    }

if executed, it may return something like::

    {
        "connection": "dbname=pencloud user=rmview host=localhost",
        "query": "SELECT uuid,email_address,first_name,last_name FROM users WHERE role='ProviderAdmin'",
        "results": [
            {
                "email_address": "pappleton@rivermeadow.com",
                "first_name": "",
                "last_name": "SPAdmin",
                "uuid": "06afdd16-319f-481e-b2ed-33944bf7227c"
            },
            {
                "email_address": "kenny@rivermeadow.com",
                "first_name": "Kenneth",
                "last_name": "Keppler",
                "uuid": "f8e3bf70-2817-4dd5-8533-6e79f685434d"
            },
            ...

then, a *drill-down* on the first returned user could be run by executing a call to::

    GET /api/1/query/get_user_by_id/id/06afdd16-319f-481e-b2ed-33944bf7227c

Note the ``$`` placeholder that needs to be replaced with the actual value of the
returned column, and the fact that the actual URL path element (``id``) does not
necessarily match the column's name (``uuid``).

The *drill-down* key will always match (case, spaces, underscores, etc.) the actual name of
the returned element, regardless of case, etc. for the DB schema.

Hence, given a query such as::

    SELECT uuid "Source UUID" , HOSTNAME hostname FROM SOURCE WHERE SOURCE.UUID=?

the *drill-down* map would looks something like::

    "drill_down": {
        "Source UUID": "/api/1/query/get_source_by_id/id/$",
        "hostname": "/api/1/query/get_hostname/hostname/$"
    }

**Knwon limitation**

It is currently not possible to substitute multiple values in a *drill-down* query, something
like::

    "drill_down": {
        "Source UUID": "/api/1/query/get_source_by_id/id/$",
        "hostname": "/api/1/query/get_hostname/hostname/$/username/$user/organization/$org"
    }

although it would be perfectly valid to use something like::

    "drill_down": {
        "Source UUID": "/api/1/query/get_source_by_id/id/$",
        "hostname": "/api/1/query/get_hostname/hostname/$/username/a_user/organization/my_org"
    }

note in this case, the additional arguments are not taken from the query result, but are fixed: all
the client needs to do, is to substitute the ``$`` placeholder with the column value.

REST API
--------

The server will provide a full API wrapper around the script functionality, returning
the response in JSON::

Get all queries
^^^^^^^^^^^^^^^

::

    GET /api/1/query

Response::

    {
        "queries": [
            "get_user", "get_migration", "get_success_duration"
        ]
    }

Execute a query
^^^^^^^^^^^^^^^

::

    query/<query_name/<param_1>/<value_1>/<param_2>/<value_2>


There can be an arbitrary number of *{param, value}* pairs, following the query's name:
the parameters' values will be substituted in the query according to the ``%(param)s`` patterns.


Given::

    "get_user_by_role": {
            "sql": "SELECT uuid,email_address,first_name,last_name FROM users WHERE role=%(role)s",
            "params": [{
                "name": "role",
                "label": "Role"
            }]
    }

We can execute the following request::

    GET /api/1/query/get_user_by_role/role/ProviderAdmin

Response::

    {
        "connection": "dbname=pencloud user=rmview host=localhost",
        "query": "SELECT uuid,email_address,first_name,last_name FROM users WHERE role='ProviderAdmin'",
        "results": [
            {
                "email_address": "pappleton@rivermeadow.com",
                "first_name": "",
                "last_name": "SPAdmin",
                "uuid": "06afdd16-319f-481e-b2ed-33944bf7227c"
            },
            {
                "email_address": "kenny@rivermeadow.com",
                "first_name": "Kenneth",
                "last_name": "Keppler",
                "uuid": "f8e3bf70-2817-4dd5-8533-6e79f685434d"
            },
            {
                "email_address": "rtsai@rivermeadow.com",
                "first_name": "Robert",
                "last_name": "Tsai",
                "uuid": "ca043832-c2b6-45f8-b0ad-3ea416336e39"
            },
            {
                "email_address": "rheaton@rivermeadow.com",
                "first_name": "Rich",
                "last_name": "Heaton",
                "uuid": "5a24565a-571c-48a0-b205-43291121d7c3"
            },
            {
                "email_address": "eric.culp@poweredbypeak.com",
                "first_name": "None",
                "last_name": "None",
                "uuid": "b43627bd-8a3c-45c0-8666-520ac4d758f5"
            }
        ],
        "rowcount": 5,
        "timestamp": "2013-07-24T16:24:24.777920",
        drill_down: {
            "email_address": "/api/1/query/get_user_by_email/email/$"
        }
    }

Create a new query
^^^^^^^^^^^^^^^^^^

::

    POST /api/1/query/my_get_user

    {
        "sql": "SELECT last_name, email_address FROM USERS WHERE UUID=%(id)s AND first_name=%(name)s",
        "drill_down": {
            "email_address": "/api/1/query/get_user_by_email/email/$"
        },
        "params": [
            {
                "label": "User UUID",
                "name": "id"
            },
            {
                "label": "First Name",
                "name": "name"
            }
        ]
    }

Response::

    201 CREATED

    <no body>

Modify an existing query
^^^^^^^^^^^^^^^^^^^^^^^^

::

    PUT /api/1/query/my_get_user

    {
        "sql": "SELECT FIRST_NAME, LAST_NAME FROM USER WHERE ID=%(id)s",
        "params": [
            {
                "label": "User UUID",
                "name": "id"
            }
        ]
    }

Response::

    200 OK

    <no body>

This will return a ``404 NOT FOUND`` if the named query does not exist or a
``406 BAD REQUEST`` if the format of the body does not meet the specification.

Delete a query
^^^^^^^^^^^^^^

::

    DELETE /api/1/query/query_to_delete

Response::

    205 RESET CONTENT

    <empty body>

Get a query details
^^^^^^^^^^^^^^^^^^^

::

    GET /api/1/info/<query>

Response::

    200 OK

    JSON full body of the query

For example, given this entry in the ``queries.json`` file::

    {
        "get_user": {
            "sql": "SELECT FIRST_NAME, LAST_NAME FROM USER WHERE ID=%(id)s",
            "params": [
                {
                    "label": "User UUID",
                    "name": "id"
                }
            ]
            "drill_down": {
                "FIRST_NAME": "/api/1/query/get_user_by_name/name/$"
            }
        },
        ... other queries
    }

The following request::

    GET /api/1/info/get_user

would get back::

    {
        "name": "get_user"
        "sql": "SELECT FIRST_NAME, LAST_NAME FROM USER WHERE ID=%(id)s",
        "params": [
            {
                "label": "User UUID",
                "name": "id"
            }
        ]
        "drill_down": {
            "FIRST_NAME": "/api/1/query/get_user_by_name/name/$"
        }
    }

Get ALL queries' details
^^^^^^^^^^^^^^^^^^^^^^^^

::

    GET /api/1/info

Response::

    200 OK

    JSON full bodies of all the queries

See above_ for an example.

.. _above: Get a query details


Installation
------------

Build
^^^^^

**Snooper** is packaged as an EGG, to build::

    python setup.py bdist_egg

this will generate a ``snooper-x.x.xxx-py2.7.egg`` where ``x.x.xxx`` is the release
version no. (set in ``src/snooper.py`` ``VERSION``).

Installation
^^^^^^^^^^^^

We recommend the use of ``virtualenv`` and once activated, it's just a matter of running::

    pip install ./snooper-x.x.xxx-py2.7.egg

**NOTE** this currently does not work due to some mysterious version error with ``pip``

**Do this instead**

1. build a virtual environment and activate it
2. obtain the latest ``requirements.txt`` from the github repo
3. run ``pip install -r requirements.txt``
4. download the ``snooper-x.x.xxx-py2.7.egg`` file from our repo
5. run ``easy_install snooper-x.x.xxx-py2.7.egg``

It's ugly, but no one ever said that Python had to be as good as Java, after all.

# TODO: update the above with actual locations once I finalize them

How-To configure PostgreSQL
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Follow the instructions here_

.. _here: http://www.cyberciti.biz/tips/postgres-allow-remote-access-tcp-connection.html

But essentially:

1. edit the configuration file::

    # vim /var/lib/pgsql/9.2/datapg_hba.conf

   add this line::

    host    all  all  10.10.0.0/16  trust

2. ensure the server is listening on all ports::

    # vim /var/lib/pgsql/9.2/postgresql.conf

   ensure this line is present::

    listen_addresses = '*'    # what IP address(es) to listen on;

3. restart Postgres::

    # service postgresql-9.2 restart
