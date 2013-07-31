#!/usr/bin/env python

__author__ = 'Marco Massenzio (marco@rivermeadow.com)'

import argparse
import ConfigParser
import datetime
import itertools
import json
import psycopg2
import psycopg2.errorcodes
import re
import sys


CONF = 'snooper.conf'


class DbSnooper(object):
    """ This class enables execution of arbitrary queries against a given DB

        Usage: create this class with a configuration dict specifying the host, db,
        etc. and optionally a query to execute, then call ```execute()``` and obtain the results
        (a query can be passed at that point too).
    """

    def __init__(self, conf, query=None, params=None):
        """ Initializes this snooper with a configuration dict::

            db - the database name
            user - user name used to authenticate
            password - password used to authenticate
            host - database host address (defaults to UNIX socket if not provided)
            port - connection port number (defaults to 5432 if not provided)

            @param conf: contains the host, port, db, user, etc to connect to the DB
            @see http://www.initd.org/psycopg/docs/module.html

            @param params: params for the query
            @type params: dict

            @param query: the SQL query to execute, optionally with named arguments
            @type query: string
        """
        port = int(conf.get('port')) if conf.get('port') else None
        try:
            self._conn = psycopg2.connect(database=conf['db'],
                                          user=conf.get('user'),
                                          password=conf.get('password'),
                                          host=conf['host'],
                                          port=port)
        except psycopg2.Error as e:
            msg = 'Could not connect to DB'
            if e.pgerror:
                msg += ': %s' % e.pgerror
            if e.pgcode:
                msg += ' [%s]' % psycopg2.errorcodes.lookup(e.pgcode)
            raise RuntimeError(msg)

        self._query = query
        self._params = params
        self._cur = self._conn.cursor()

    @property
    def query(self):
        return self._query

    @query.setter
    def query(self, query):
        self._query = query

    @property
    def params(self):
        return self._params

    @params.setter
    def params(self, params):
        """ The named parameters for the query, as a map of name, values pairs

            @type params: dict
        """
        self._params = params

    def execute(self):
        """ Executes the query that was passed in at construction or set afterwards

            @return: a dictionary constructed with the results (cursor) and
            augmented with some query metadata::

                {
                    "connection": "dbname=pencloud user=rmview host=localhost",
                    "query": "SELECT uuid,email_address,first_name,last_name FROM users
                              WHERE role='ProviderAdmin'",
                    "rowcount": 5,
                    "timestamp": "2013-07-24T16:24:24.777920",
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
                    ]
                }
            @rtype: dict
        """
        if not self._query:
            raise RuntimeError('Must specify a SQL query before attempting to execute it')
        self._cur.execute(self._query, self._params)
        # TODO: psycopg2 supports paginations, as well as retrieving results one row at a time
        results = self._cur.fetchall()
        return self._res_to_dict(results)

    def _res_to_dict(self, cursor):
        res = {
            'connection': re.sub('\s+password=\w+', '', self._conn.dsn),
            'timestamp': datetime.datetime.now().isoformat(),
            'query': self._query % self._params if self._params else self._query,
            'rowcount': self._cur.rowcount
        }
        # add some metadata about the connection
        if cursor:
            results = []
            for row in cursor:
                another = {}
                for i, col in enumerate(row):
                    another[self._cur.description[i].name] = str(col)
                results.append(another)
            res['results'] = results
        return res


def parse_args():
    """ Parses the command line arguments and returns a configuration dict

    @return: a configuration dict
    """
    parser = argparse.ArgumentParser(description='SQL command line execution tool')
    parser.add_argument('--queries',
                        help='an optional input file (JSON) defining a set of SQL queries')
    parser.add_argument('--out', help='an optional output file')
    parser.add_argument('--host', help='the host to run the query against (must be '
                                       'running the Postgres server and have the external port '
                                       'accessible',
                        default='localhost')
    parser.add_argument('--format', default='JSON', help='the format for the output')
    parser.add_argument('--query', '-q', help='used in conjunction with --queries, '
                                              'specifies the named query to run')
    parser.add_argument('--list', '-l', action='store_true',
                        help='Lists all available queries in the files specified with '
                             'the --queries flag and exits')
    parser.add_argument('--env', default='dev', help='the section in the %s configuration file, '
                                                     'from which to take the connection '
                                                     'configuration parameters' % (
                                                         CONF,))
    parser.add_argument('--debug', action='store_true', default=False,
                        help='If set, the server will be run in debug mode: do NOT use in '
                             'production')
    parser.add_argument('query_params', metavar='param', nargs='*', help='positional parameters '
                                                                         'for the query')
    return parser.parse_args()


def parse_queries(filename):
    """ Reads in the filename and parses into a dictionary of named queries

        @return: a dict where each (named) entry is a query
        @rtype: dict
    """
    # TODO: currently the implementation of this is trivial, we should implement more
    # sophisticated transformations
    try:
        with open(filename) as queries_file:
            parsed_json = json.load(fp=queries_file)
            if parsed_json:
                return parsed_json.get("queries")
    except Exception, ex:
        print 'Could not parse queries file %s: %s' % (filename, ex)


def parse_query_params(named_params):
    """ Parses a list of name, value parameter values and builds a dict that can be passed to
        sycopg2 ```execute()``` method.

        See http://www.initd.org/psycopg/docs/usage.html#passing-parameters-to-sql-queries
    """
    # islice() takes a sequence and returns the items from start to stop, every step
    # the code below cycles to the passed in params and makes a name/value pair
    # see: http://docs.python.org/2/library/itertools.html#itertools.islice
    return dict(itertools.izip(itertools.islice(named_params, 0, None, 2),
                               itertools.islice(named_params, 1, None, 2)))


def print_queries(queries):
    """ Prints out the available queries as '<name> :: <sql query>' lines"""
    for query in queries:
        print "%20s :: %s" % (query, queries[query].get("sql"))


def config_connection(conf):
    """ Returns a connection configuration dict, based on the chosen configuration.

     Uses the ```CONF``` file to retrieve the appropriate DB connection configuration parameters,
      based on the chosen ```--config``` option
    """
    config = ConfigParser.ConfigParser()
    config.read(CONF)
    res = {'host': conf.host,
           'db': config.get(conf.env, 'db'),
           'user': config.get(conf.env, 'user'),
           'password': config.get(conf.env, 'password')
    }
    return res


def main():
    """ Runs the specified query

        @return: the query result or None, if the output is sent to a file
    """
    conf = parse_args()
    query_to_run = None
    query_params = None
    if conf.queries:
        queries = parse_queries(conf.queries)
        if conf.query:
            if queries.get(conf.query):
                query_to_run = queries.get(conf.query).get("sql")
                query_params = parse_query_params(conf.query_params)
        elif conf.list:
            print_queries(parse_queries(conf.queries))
            exit(0)
    elif len(conf.query_params) > 0:
        query_to_run = conf.query_params[0]
    else:
        raise RuntimeError('The query must be specified either by using the --query option, '
                           'or on the command line')
    print 'Executing "{0:s}"  ::  {1:s}'.format(conf.query, query_to_run)
    connection = config_connection(conf)
    snooper = DbSnooper(conf=connection, query=query_to_run, params=query_params)
    results = snooper.execute()
    if conf.out:
        print 'Saving {0:d} results to {1:s}'.format(results.get('rowcount', 0), conf.out)
        with open(conf.out, 'w') as results_file:
            json.dump(results, results_file,
                      sort_keys=True,
                      indent=4,
                      separators=(',', ': '))
    else:
        return json.dumps(results, sort_keys=True, indent=4, separators=(',', ': '))


if __name__ == '__main__':
    try:
        out = main()
        if out:
            print out
    except RuntimeError, e:
        print >> sys.stderr, 'Error encountered while querying DB: %s' % e
