#!/usr/bin/env python
#
# Copyright (c) 2013 RiverMeadow Software Inc. All rights reserved.



__author__ = 'Marco Massenzio (marco@rivermeadow.com)'

"""
    This is a thin REST layer on top of snooper.py

    It will expose a limited set of REST APIs to interact with  the underlying ```snooper```
    functionality.

    See README.rst for more info about the API and the general functionality.
"""


import flask
from flask import Flask, abort, redirect, session, send_file, make_response
from flask.ext import restful
from flask.ext.restful import reqparse
import json
import logging
import snooper
from werkzeug.local import LocalProxy


SECRET_KEY = '#3K5h43Hl53&s0Bod62y$%C34t6oDv3NN47Oz24GT7$3TFJWDS5yX7E7&a4994e0'
REST_BASE_URL = '/api/1/query'


class RestResource(restful.Resource):
    """
        A base class for all resources, where we can stash the logger and the configuration objects
    """

    _conf = {}
    _logger = None


class QueryAllResource(RestResource):
    def get(self):
        queries = []
        all_queries = snooper.parse_queries(self._conf.queries)
        for query_name, query_value in all_queries.iteritems():
            args = query_value.get('params', [])
            queries.append({query_name: args})
        return {"queries": queries}


class QueryResource(RestResource):
    def get(self, query, args=None):
        query = snooper.parse_queries(self._conf.queries).get(query)
        if query:
            params = None
            if args:
                params = snooper.parse_query_params(args.split('/'))
            res = self.run_query(query.get("sql"), params)
            res["drill_down"] = query.get("drill_down")
            return res
        else:
            self._logger.error('Could not find query %s', query)
            abort(404)

    def run_query(self, query, params=None):
        db_conn.query = query
        db_conn.params = params
        self._logger.debug('Executing query: {} - with params: {}'.format(db_conn.query,
                                                                          db_conn.params))
        res = db_conn.execute()
        self._logger.debug('Found {} results'.format(res["rowcount"]))
        return res


class PromotionCodesResource(RestResource):
    REQUEST_ARGS = ['cloud', 'provider', 'cloud_type', 'created_by']

    def __init__(self):
        parser = reqparse.RequestParser()
        for arg in PromotionCodesResource.REQUEST_ARGS:
            parser.add_argument(arg, location='form')
        self._parser = parser

    def _check_args_exist_in_request(self, args):
        for required in PromotionCodesResource.REQUEST_ARGS:
            if not required in args:
                self._logger.error("Argument %s not found in the request arguments" % (required,))
                return False
        return True

    def post(self, count):
        args = self._parser.parse_args()
        if not self._check_args_exist_in_request(args):
            self._logger.error("All required args should be passed in the request")
            abort(406)
        try:
            mgr = snooper.CouponsManager(args['provider'],
                                         args['cloud'],
                                         args['cloud_type'],
                                         args['created_by'], db=db_conn)
            filename = '/tmp/coupons.csv'
            mgr.make_coupons(count, filename=filename)
            return send_file(filename, as_attachment=True)
        except Exception as e:
            self._logger.error(e.message)
            return render_template('err_msg.html', title="Error creating codes", message=e.message)


def render_template(template, **kwargs):
    """ Helper method to return the given template

        This is needed due to the nefarious conflict between assumed defaults in Flask RESTful and
        Flask itselfl.
    """
    response = make_response(flask.render_template(template, **kwargs))
    response.headers["Content-type"] = "text/html"
    return response


def get_db():
    db = getattr(flask.g, '_database', None)
    if not db:
        conf = snooper.parse_args()
        db = snooper.DbSnooper(conf=snooper.config_connection(conf))
        flask.g._database = db
    return db

db_conn = LocalProxy(get_db)


def build_routes(api, conf, logger):
    """ Sets up the routes for the REST API.

        @param api: the Flask REST object to add routes to
        @type api: L{restful.Api}
    """
    RestResource._conf = conf
    RestResource._logger = logger

    api.add_resource(QueryAllResource, REST_BASE_URL)
    api.add_resource(QueryResource, '/'.join([REST_BASE_URL, '<query>', '<path:args>']),
                     '/'.join([REST_BASE_URL, '<query>']))
    api.add_resource(PromotionCodesResource, '/'.join(['', 'codes', '<int:count>']))


def run_server():
    """ The main server app, starts up Flask, sets up the routes and handles requests
    """
    conf = snooper.parse_args()
    app = Flask('snooper')
    if not conf.debug:
        # By default, in non-debug mode, the app logger does not log anything
        # we enable it here to log DEBUG level to Console
        app.logger.setLevel(logging.DEBUG)
        app.logger.addHandler(logging.StreamHandler())
    api = restful.Api(app)
    build_routes(api, conf, app.logger)

    @app.errorhandler(404)
    def redirect_to_UI(error):
        print '--- Not found: ', error
        return render_template('index.html')

    # @app.errorhandler(500)
    # def handle_ex(error):
    #     print '>>>>> Error: ', error
    #     app._logger.error(error)
    #     return render_template('err_msg.html')

    app.run(debug=conf.debug, host='0.0.0.0')

if __name__ == '__main__':
    run_server()
