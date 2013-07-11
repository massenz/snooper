====================
SQL Script execution
====================

:Date: 2013-07-11
:Author: M. Massenzio
:Version: 0.1

Use Case
--------

As a RM staff I need to explore (or modify) the state of some of the Tables in the Postgres DB
by running an arbitrary query against a dev (or Prod) instance.

There may also be a set of predefined queries that may be run automatically; further, these
predefined queries may have a number of parameters that will have to be substituted before
executing them.

The output of the script must be suitable for both human and machine (eg, piping) consumption

Implementation
--------------

This is a python script that takes a number of command-line arguments, constructs the query and
then executes it against a specified RM VM instance.

The output format will initially be JSON, but should be possible for the user to choose from a
predefined set (eg, CSV, HTML table, etc.)

Command-line arguments
^^^^^^^^^^^^^^^^^^^^^^

::

    --queries   an optional input file (JSON) defining a set of SQL queries
    --out       an optional output file
    --host      the host to run the queries agains (default: localhost)
    --format    the output format (currently only JSON, default, supported)
