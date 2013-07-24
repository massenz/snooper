====================
SQL Script execution
====================

:Date: 2013-07-11
:Author: M. Massenzio
:Version: 0.1

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

::

    --queries   an optional input file (JSON) defining a set of SQL queries
    --out       an optional output file
    --host      the host to run the queries agains (default: localhost)
    --format    the output format (currently only JSON, default, supported)
    --query, -q the query to run (named, from the ``queries`` file)
    --list, -l  lists the queries by name and exits
    --env        the parameters for the DB connection (db, user, password) are defined in a
                 configuration file, for different environments (eg, `dev` or `prod`): this defines
                 the section of the configuration file to use



If the query to run has named arguments, then those should be passed in (for now, I will only
support `positional` arguments).

For example, say you want to run the ``get_user`` query from the ``queries.json`` file::

    {
        "queries": {
            "get_user": "SELECT USERNAME, PASSWORD FROM USER WHERE ID=?",
            ...
        }
    }

then one would invoke the script as follows::

    snooper --queries queries.json --host 10.10.121.99 --query get_user 99

the script would then run the query as follows::

    SELECT USERNAME, PASSWORD FROM USER WHERE ID='99'

Alternatively, the script can be used to run an arbitrary SQL query from the command line::

    snooper --host 10.10.121.99 'SELECT USERNAME, PASSWORD FROM USER WHERE ID=99'

Please note it's an **error** to pass both the ``--queries`` argument and a query (in this case,
the query literal would be incorrectly interpreted as one of the query's positional parameters).

Connection parameters
^^^^^^^^^^^^^^^^^^^^^

These are taken from a configuration file (``snooper.conf``) and grouped by ``environments``,
as in::

    # Connection configuration for Snooper

    [dev]
    db = mydb
    user = uzer
    password = duba

    [prod]
    db = pencloud
    user = zooz
    password = blaaaz

Use the ``--env`` command-line arg to specify a given environment (``dev`` is used by default).

REST API
--------

The server will provide a minimalist API wrapper around the script functionality, returning
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

    GET /api/1/query/get_user?arg=ProviderAdmin

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
        "timestamp": "2013-07-24T16:24:24.777920"
    }

Create a new query
^^^^^^^^^^^^^^^^^^

::

    POST /api/1/query

    {
        "name": "my_get_user",
        "sql": "SELECT USERNAME, PASSWORD FROM USER WHERE ID=?",
        "num_args": 1
    }

Modify an existing query
^^^^^^^^^^^^^^^^^^^^^^^^

::

    PUT /api/1/query/my_get_user

    {
        "name": "my_get_user",
        "sql": "SELECT FIRST_NAME, LAST_NAME FROM USER WHERE ID=?",
        "num_args": 1
    }

Get a query details
^^^^^^^^^^^^^^^^^^^

::

    GET /api/1/query/get_user/details

Response::

    {
        "name": "get_user"
        "query": "SELECT uuid,email_address,first_name,last_name FROM users WHERE role=?",
        "num_args": 1
    }
