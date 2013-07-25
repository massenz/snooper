#!/usr/bin/env python
#
# Copyright (c) 2013 RiverMeadow Software Inc. All rights reserved.
import json
import logging

__author__ = 'Marco Massenzio (marco@rivermeadow.com)'


import flask
from flask import Flask, abort, session
import snooper


app = Flask('snooper')
conf = snooper.parse_args()
db_conn = snooper.DbSnooper(conf=snooper.config_connection(conf))


@app.route('/api/1/query')
def get_all_queries():
    queries = []
    for query in snooper.parse_queries(conf.queries):
        queries.append(query)
    return json.dumps({"queries": queries})

@app.route('/api/1/query/<query>')
def execute_query(query):
    query = snooper.parse_queries(conf.queries).get(query)
    if query:
        res = db_conn.execute(query=query)
        app.logger.debug('Res: %s', res)
        return json.dumps(res)
    else:
        app.logger.error('Could not find query %s', query)
        abort(404)

if __name__ == '__main__':
    #logging.basicConfig()
    if not conf.debug:
        # By default, in non-debug mode, the app logger does not log anything
        app.logger.setLevel(logging.DEBUG)
        app.logger.addHandler(logging.StreamHandler())
    app.secret_key = '#3K5h43Hl53&s0Bod62y$%C34t6oDv3NN47Oz24GT7$3TFJWDS5yX7E7&a4994e0'
    app.run(debug=conf.debug)
    flask.g['db_conn'] = db_conn
