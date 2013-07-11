import ConfigParser
import datetime

__author__ = 'marco'

import argparse
import json
import psycopg2
import psycopg2.errorcodes
import re


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

            @param params: Not currently used, params for the query
            # TODO: seems a better approach then the current string replacement
        """
        port = int(conf.get('port')) if conf.get('port') else None
        try:
            self._conn = psycopg2.connect(database=conf['db'],
                                          user=conf.get('user'),
                                          password=conf.get('password'),
                                          host=conf['host'],
                                          port=port)
        except psycopg2.Error as e:
            msg = 'Could not connect to DB: %s' % e.pgerror
            if e.pgcode:
                msg.append(' [%s]' % psycopg2.errorcodes.lookup(e.pgcode))
            raise RuntimeError(msg)

        self._query = query
        self._cur = self._conn.cursor()
        self._results = None

    def execute(self, query=None):
        if not query and not self._query:
            raise RuntimeError('Must specify a SQL query before attempting to execute it')
        # this will override the predefined self._query, if already defined:
        if query:
            self._query = query
        self._cur.execute(self._query)
        # TODO: psycopg2 supports paginations, as well as retrieving results one row at a time
        self._results = self._cur.fetchall()
        return self._res_to_dict()

    def _res_to_dict(self):
        res = {}
        # add some metadata about the connection
        res['connection'] = re.sub('\s+password=\w+', '', self._conn.dsn)
        res['timestamp'] = datetime.datetime.now().isoformat()
        res['query'] = self._query
        res['rowcount'] = self._cur.rowcount
        if self._results:
            results = []
            for row in self._results:
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
    parser.add_argument('--queries', default='queries.json',
                        help='an optional input file (JSON) defining a set of SQL queries')
    parser.add_argument('--out', help='an optional output file')
    parser.add_argument('--host', required=True, help='the host to run the query against (must be '
                        'running the Postgres server and have the external port accessible',
                        default='localhost')
    parser.add_argument('--format', default='JSON', help='the format for the output')
    parser.add_argument('--query', '-q', help='used in conjunction with --queries, '
                                              'specifies the named query to run')
    parser.add_argument('--list', '-l', action='store_true',
                        help='Lists all available queries in the files specified with '
                             'the --queries flag and exits')
    parser.add_argument('--config', '-c', default='dev', help='the section in the %s configuration '
                        'file, from which to take the connection configuration parameters' % (CONF,))
    parser.add_argument('query_params', metavar='param', nargs='*',
                                                      help='positional parameters '
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


def replace_params(query, params):
    """ Replaces '?' placeholders in `query` with corresponding strings in `params`

        @type query: string
        @type params: list
    """
    def replace(match_obj):
        rep = params[0]
        params.remove(rep)
        return rep
    return re.sub('\?', replace, query)


def list_queries(queries):
    """ Prints out the available queries"""
    for name, query in queries.iteritems():
        print "%20s :: %s" % (name, query)


def config_connection(conf):
    """ Returns a connection configuration dict, based on the chosen configuration.

     Uses the ```CONF``` file to retrieve the appropriate DB connection configuration parameters,
      based on the chosen ```--config``` option
    """
    config = ConfigParser.ConfigParser()
    config.read(CONF)
    res = {'host': conf.host,
           'db': config.get(conf.config, 'db'),
           'user': config.get(conf.config, 'user'),
           'password': config.get(conf.config, 'password'),
    }
    return res


def main():
    conf = parse_args()
    if conf.queries:
        if conf.query:
            query_to_run = parse_queries(conf.queries).get(conf.query)
            if query_to_run:
                query_to_run = replace_params(query_to_run, conf.query_params)
        elif conf.list:
            list_queries(parse_queries(conf.queries))
            exit(0)
    else:
        query_to_run = conf.query_params[0]
    print 'Executing "%s"  ::  %s' % (conf.query, query_to_run)
    connection = config_connection(conf)
    snooper = DbSnooper(conf=connection, query=query_to_run)
    print json.dumps(snooper.execute(),
                     sort_keys=True,
                     indent=4,
                     separators=(',', ': '))


if __name__ == '__main__':
    main()
