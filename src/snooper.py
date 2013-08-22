#!/usr/bin/env python

__author__ = 'Marco Massenzio (marco@rivermeadow.com)'

import argparse
import ConfigParser
import datetime
import itertools
import json
import psycopg2
import psycopg2.errorcodes
import random
import re
import string
import sys
import uuid

DEFAULT_PORT = 5432
""" Default Postgresql listening port"""


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
            port - connection port number (defaults to ```DEFAULT_PORT``` if not provided)

            @param conf: contains the host, port, db, user, etc to connect to the DB
            @see http://www.initd.org/psycopg/docs/module.html

            @param params: params for the query
            @type params: dict

            @param query: the SQL query to execute, optionally with named arguments
            @type query: string
        """
        port = int(conf.get('port', DEFAULT_PORT))
        try:
            self._conn = psycopg2.connect(database=conf['db'],
                                          user=conf.get('user'),
                                          password=conf.get('password'),
                                          host=conf['host'],
                                          port=port)
        except psycopg2.Error as e:
            msg = 'Could not connect to DB (%s)' % (e,)
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

    def execute(self, fetch=True):
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
        if fetch:
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

    def commit(self):
        self._conn.commit()


class CouponsManager(object):
    """ Manages the creation of coupons

    """
    # TODO: we will need to eventually add functionality to manage, delete, view etc. coupons

    PROVIDER_QUERY = "SELECT UUID \"uuid\" FROM ORGANIZATIONS WHERE NAME=%(provider)s AND " \
                     "TYPE='SERVICE_PROVIDER'"

    CLOUD_QUERY = "SELECT t.UUID \"uuid\", t.URL \"url\", t.name \"name\", " \
                  "t.target_type \"type\" FROM CLOUD_TARGETS t, ORGANIZATIONS o " \
                  "WHERE t.provider_ref = o.uuid " \
                  "AND t.NAME=%(cloud)s " \
                  "AND o.name=%(provider)s " \
                  "AND o.type='SERVICE_PROVIDER'"

    CODES_QUERY = "INSERT INTO PROMOTION_CODES " \
                  "(uuid, provider_ref, cloud_target_ref, code, count, valid," \
                  " cloud_target_name, cloud_target_type, created_by) " \
                  "VALUES " \
                  "(%(uuid)s, %(provider_ref)s, %(cloud_target_ref)s, %(code)s, %(count)s," \
                  " %(valid)s,%(cloud_target_name)s, %(cloud_target_type)s, %(created_by)s)"

    USER_QUERY = "SELECT UUID FROM USERS WHERE EMAIL_ADDRESS=%(email)s"

    def __init__(self, provider, cloud, cloud_type, created_by, db=None, conf=None):
        """ Initializes a Coupons Manager

            @param provider:  the name of the service provider
            @param cloud: the name of the target cloud
            @param cloud_type: the type of cloud (eg, VCLOUD)
            @param created_by: the user that will be responsible for coupon creation
            @param conf: a dict-like configuration object that defines the connection
                    configurations for the database.
                    See ```config_connnection()``` for details about the connection configuration.
            @type conf: dict

            @param db: a connection to a postgresql instance, if None, it will try to create a
                new one using connection configuration parameters from ```conf```
            @type db: L{DbSnooper}
        """
        self.provider = provider
        self.cloud_target = cloud
        self.cloud_type = cloud_type
        self.created_by = created_by
        self._db = db or DbSnooper(conf=config_connection(conf))

    def _generate_code(self, sep='-', segments=3, segment_len=4,
                       chars=string.digits + string.ascii_uppercase):
        parts = [''.join(random.choice(chars) for x in range(segment_len)) for y in range(segments)]
        return sep.join(parts)

    def _get_provider_uuid(self):
        """ Finds the UUID for the Service Provider
        """
        self._db.query = CouponsManager.PROVIDER_QUERY
        self._db.params = {'provider': self.provider}
        res = self._db.execute()
        if res['rowcount'] > 0:
            return res['results'][0]['uuid']

    def _get_target_cloud_info(self):
        """ Collects information about a given cloud target

            @return: a dict with (uuid, url, name, type) for the target cloud, if found
            @rtype: dict or None
        """
        self._db.query = CouponsManager.CLOUD_QUERY
        self._db.params = {
            'cloud': self.cloud_target,
            'provider': self.provider,
        }
        res = self._db.execute()
        if res['rowcount'] > 0:
            info = res['results'][0]
            return info

    def _get_user_id(self, email):
        """ Looks up the user by email

            @return: the UUID of the user
            @rtype: string
        """
        self._db.query = CouponsManager.USER_QUERY
        self._db.params = {
            'email': email
        }
        res = self._db.execute()
        if res['rowcount'] > 0:
            return res['results'][0]['uuid']

    def make_coupons(self, count, filename=None):
        """ Creates ```count`` coupons, saving them to db, and optionally storing them to a CSV
        file

        """
        if not self.provider or not self.cloud_target or not self.created_by:
            raise RuntimeError(
                '''To generate coupons, you must specifiy the name of the Service Provider,
                   the Cloud Target and the user that creates this promotion codes.
                   For more info run: snooper --help or see
                     https://github.com/RiverMeadow/encloud/blob/develop/docs/coupons.rst''')
        user_id = self._get_user_id(self.created_by)
        if not user_id:
            raise RuntimeError('User %s could not be found in the system' % (self.created_by,))
        coupon_values = {
            'count': 1,
            'valid': True,
            'created_by': user_id
        }
        print 'Generating %d Promotion Codes for %s [%s]' % (count, self.provider,
                                                             self.cloud_target)
        provider_uuid = self._get_provider_uuid()
        if not provider_uuid:
            raise RuntimeError("Could not find the ID for provider %s" % (self.provider,))
        coupon_values['provider_ref'] = provider_uuid
        print 'Found Service Provider %s [%s]' % (self.provider, provider_uuid)

        info = self._get_target_cloud_info()
        if not info:
            # This covers the case for when a target cloud is not available, and one will be
            # created at code redemption time (eg, for vmware VHCS)
            print 'No cloud target found for %s' % (self.cloud_target,)
            coupon_values['cloud_target_ref'] = None
            coupon_values['cloud_target_name'] = self.cloud_target
            coupon_values['cloud_target_type'] = self.cloud_type
        else:
            print 'Found Cloud Target %s [%s]: %s' % (self.cloud_target, info.get('uuid'),
                                                      info.get('url'))
            coupon_values['cloud_target_ref'] = info.get('uuid')
            coupon_values['cloud_target_name'] = info.get('name')
            coupon_values['cloud_target_type'] = info.get('type')

        codes = []
        for i in range(count):
            coupon_values['uuid'] = str(uuid.uuid4())
            coupon_values['code'] = self._generate_code()
            self._db.query = CouponsManager.CODES_QUERY
            self._db.params = coupon_values
            self._db.execute(fetch=False)
            self._db.commit()
            codes.append(coupon_values['code'])
        print 'Done - generated %d coupons' % (count,)

        if filename:
            with open(filename, 'w') as coupon_list:
                metadata = {
                    'when': datetime.datetime.now().isoformat(),
                    'provider': self.provider,
                    'provider_uuid': provider_uuid,
                    'cloud_target': self.cloud_target,
                    'count': count,
                    'created_by': self.created_by
                }
                coupon_list.writelines(
                    '# RiverMeadow Software, Inc. - created %(when)s\n'
                    '#\n'
                    '# For Service Provider: %(provider)s [%(provider_uuid)s]\n'
                    '# Cloud Target: %(cloud_target)s\n'
                    '# Created by: %(created_by)s\n'
                    '#\n'
                    '# This file contains %(count)d promotion codes\n\n' % metadata)
                for code in codes:
                    coupon_list.writelines([code, '\n'])
            print 'Saved the list of codes to %s' % (filename,)
        return codes


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
                                                     'configuration parameters')
    parser.add_argument('--debug', action='store_true', default=False,
                        help='If set, the server will be run in debug mode: do NOT use in '
                             'production')
    parser.add_argument('--conf', help='The location of the configuration file which contains the'
                                       ' connection parameters', required=True)
    parser.add_argument('--coupons', type=int,
                        help='This will generate the requested number of coupons, '
                             'insert in the database and return in the --out file the list of '
                             'codes. MUST specify --provider and --cloud UUIDs')
    parser.add_argument('--provider', help='The name of the Service Provider for the coupons')
    parser.add_argument('--cloud', help='The name of the Cloud Target for the coupons; if the'
                                        ' targets does not exist, it will be used for the "name" '
                                        'field, when one will be created')
    parser.add_argument('--cloud-type', help='Optional, will be used if the Cloud Target does not'
                                             ' exist, as its "type" when it will be created')
    parser.add_argument('--created-by',
                        help='The system user that will be responsible for generating the '
                             'entitlements associated with these promotion codes: it MUST be a '
                             'valid user in the system')
    parser.add_argument('query_params', metavar='param', nargs='*', help='positional parameters '
                                                                         'for the query')
    return parser.parse_args()


def parse_queries(filename):
    """ Reads in the filename and parses into a dictionary of named queries

        @return: a dict where each (named) entry is a query
        @rtype: dict
    """
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

     Reads in a configuration file to retrieve the appropriate DB connection configuration
     parameters.

     The passed in L{ArgumentParser} configuration object, must contain at a minimum the
     following attributes:

        ``conf``    the configuration file name
        ``env``     the section in the config file to use ("environment")

     The "environment"  will have have the following values defined: 'db',
     'user' and 'password' for the DB connection (and, optionally, 'host' - however,
     the hostname passed in at the CLI [--host] will take precedence, if provided).

     @return: a configuration dictionary that can be used to construct a L{DbSnooper} object
     @rtype: dict
    """
    config = ConfigParser.ConfigParser({'port': DEFAULT_PORT,
                                        'host': conf.host,
                                        'user': None,
                                        'password': ''})
    config.read(conf.conf)
    res = {'host': config.get(conf.env, 'host'),
           'port': config.get(conf.env, 'port', raw=True),
           'db': config.get(conf.env, 'db'),
           'user': config.get(conf.env, 'user'),
           'password': config.get(conf.env, 'password')
    }
    return res


def run_query():
    """ Runs the specified query

        @return: the query result or None, if the output is sent to a file
    """
    conf = parse_args()
    if conf.coupons:
        mgr = CouponsManager(conf.provider,
                             conf.cloud,
                             conf.cloud_type,
                             conf.created_by,
                             conf=conf)
        codes = mgr.make_coupons(conf.coupons, conf.out)
        if not conf.out:
            return codes
        return
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


def main():
    try:
        out = run_query()
        if out:
            print out
    except RuntimeError, e:
        print >> sys.stderr, 'Error encountered while querying DB: %s' % e


if __name__ == '__main__':
    main()
