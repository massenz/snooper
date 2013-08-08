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
from flask import Flask, abort, redirect, session
from flask.ext import restful
import json
import logging
import snooper


SECRET_KEY = '#3K5h43Hl53&s0Bod62y$%C34t6oDv3NN47Oz24GT7$3TFJWDS5yX7E7&a4994e0'
REST_BASE_URL = '/api/1/query'

# Globals are evil, but apparently there is no (easy) way around this in Flask
# The good news is, we can keep this as a 'thin wrapper' around a truly OO design,
# keeping the routes as the only place where we expose everything at module level
#
# The downside is that we will need to create Global objects here, for all the entities that are
# needed for each route.
app = Flask('snooper')
api = restful.Api(app)
conf = snooper.parse_args()
db_conn = snooper.DbSnooper(conf=snooper.config_connection(conf))


class QueryAllResource(restful.Resource):

    def get(self):
        queries = []
        for query in snooper.parse_queries(conf.queries):
            queries.append(query)
        return {"queries": queries}


class QueryResource(restful.Resource):
    def get(self, query, args=None):
        query = snooper.parse_queries(conf.queries).get(query)
        if query:
            db_conn.query = query.get("sql")
            db_conn.params = snooper.parse_query_params(args.split('/'))
            app.logger.debug('Executing query: {} - with params: {}'.format(db_conn.query,
                                                                            db_conn.params))
            res = db_conn.execute()
            app.logger.debug('Found {} results'.format(res["rowcount"]))
            res["drill_down"] = query.get("drill_down")
            return res
        else:
            app.logger.error('Could not find query %s', query)
            abort(404)


class SnooperResources(object):
    def __init__(self, api):
        """ Sets up the routes for the REST API.

            @param api: the Flask REST object to add routes to
            @type api: L{restful.Api}
        """
        api.add_resource(QueryAllResource, REST_BASE_URL)
        api.add_resource(QueryResource, '/'.join([REST_BASE_URL, '<query>', '<path:args>']))


@app.errorhandler(404)
def redirect_to_UI(error):
    print '404: ', error
    q = session
    return redirect('http://localhost')

if __name__ == '__main__':
    if not conf.debug:
        # By default, in non-debug mode, the app logger does not log anything
        # we enable it here to log DEBUG level to Console
        app.logger.setLevel(logging.DEBUG)
        app.logger.addHandler(logging.StreamHandler())
    routes = SnooperResources(api)
    app.run(debug=conf.debug)
