import re

__author__ = 'marco'

import argparse
import json



def parse_args():
    parser = argparse.ArgumentParser(description='SQL command line execution tool')
    parser.add_argument('--queries', default='queries.json',
                        help='an optional input file (JSON) defining a set of SQL queries')
    parser.add_argument('--out', help='an optional output file')
    parser.add_argument('--host', help='the host to run the query against (must be running the '
                                       'Postgres server and have the external port accessible',
                        default='localhost')
    parser.add_argument('--format', default='JSON', help='the format for the output')
    parser.add_argument('--query', '-q', help='used in conjunction with --queries, '
                                              'specifies the named query to run')
    parser.add_argument('--list', '-l', action='store_true',
                        help='Lists all available queries in the files specified with '
                             'the --queries flag')
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


if __name__ == '__main__':
    main()
