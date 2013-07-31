#!/usr/bin/env python
#
# Copyright (c) 2013 RiverMeadow Software Inc. All rights reserved.
import json
import logging

__author__ = 'Marco Massenzio (marco@rivermeadow.com)'

"""
    This is a thin REST layer on top of snooper.py

    It will expose a limited set of REST APIs to interact with  the underlying ```snooper```
    functionality.

    See README.rst for more info about the API and the general functionality.
"""


import flask
from flask import Flask, abort
import snooper


SECRET_KEY = '#3K5h43Hl53&s0Bod62y$%C34t6oDv3NN47Oz24GT7$3TFJWDS5yX7E7&a4994e0'

# Globals are evil, but apparently there is no (easy) way around this in Flask
# The good news is, we can keep this as a 'thin wrapper' around a truly OO design,
# keeping the routes as the only place where we expose everything at module level
#
# The downside is that we will need to create Global objects here, for all the entities that are
# needed for each route.
app = Flask('snooper')
conf = snooper.parse_args()
db_conn = snooper.DbSnooper(conf=snooper.config_connection(conf))


@app.route('/api/1/query')
def get_all_queries():
    queries = []
    for query in snooper.parse_queries(conf.queries):
        queries.append(query)
    return json.dumps({"queries": queries})

@app.route('/api/1/query/<query>/<path:args>')
def execute_query(query, args=None):
    query = snooper.parse_queries(conf.queries).get(query)
    if query:
        db_conn.query = query.get("sql")
        db_conn.params = snooper.parse_query_params(args.split('/'))
        app.logger.debug('Executing query: {} - with params: {}'.format(db_conn.query,
                                                                        db_conn.params))
        res = db_conn.execute()
        app.logger.debug('Found {} results'.format(res["rowcount"]))
        res["drill_down"] = query.get("drill_down")
        return json.dumps(res)
    else:
        app.logger.error('Could not find query %s', query)
        abort(404)

if __name__ == '__main__':
    if not conf.debug:
        # By default, in non-debug mode, the app logger does not log anything
        # we enable it here to log DEBUG level to Console
        app.logger.setLevel(logging.DEBUG)
        app.logger.addHandler(logging.StreamHandler())
    app.run(debug=conf.debug)
