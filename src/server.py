#!/usr/bin/env python
#
# Copyright (c) 2013 RiverMeadow Software Inc. All rights reserved.
import urllib


__author__ = 'Marco Massenzio (marco@rivermeadow.com)'

"""
    This is a thin REST layer on top of snooper.py

    It will expose a limited set of REST APIs to interact with  the underlying ```snooper```
    functionality.

    See README.rst for more info about the API and the general functionality.
"""

import flask
from flask import (Flask,
                   abort,
                   redirect,
                   session,
                   send_file,
                   make_response,
                   request, url_for)
from flask.ext import restful
from flask.ext.restful import reqparse
import json
import logging
import snooper
from werkzeug.local import LocalProxy


SECRET_KEY = '#3K5h43Hl53&s0Bod62y$%C34t6oDv3NN47Oz24GT7$3TFJWDS5yX7E7&a4994e0'
REST_BASE_URL = '/api/1/query'

conf = snooper.parse_args()
app = Flask('snooper')
if not conf.debug:
    # By default, in non-debug mode, the app logger does not log anything
    # we enable it here to log DEBUG level to Console
    app.logger.setLevel(logging.DEBUG)
    app.logger.addHandler(logging.StreamHandler())


@app.errorhandler(404)
def redirect_to_ui(error):
    return render_template('index.html')


@app.errorhandler(Exception)
def handle_ex(exception):
    app.logger.exception(exception)
    return render_error('Application Error', str(exception))


@app.route('/test')
def test():
    """Used to test correct re-routing of application exceptions"""
    raise RuntimeError("this was an error")


@app.route(REST_BASE_URL)
def get_all():
    """Gets all existing queries"""
    return json.dumps({"queries": get_all_queries()})


@app.route('/'.join([REST_BASE_URL, '<query>', '<path:args>']))
@app.route('/'.join([REST_BASE_URL, '<query>']), methods=['GET', 'POST', 'PUT', 'DELETE'])
def query_resource(query, args=None):
    if request.method in ['POST', 'PUT']:
        return upsert_query(query, is_new=(request.method == 'POST'))
    elif request.method == 'GET':
        return get(query, args)
    elif request.method == 'DELETE':
        return delete_query(query)
    else:
        return ApiException('Method {} not implemented'.format(request.method))


@app.route('/error/<title>/<message>', methods=['POST'])
def post_error_message(title, message):
    title = title.replace('+', ' ')
    message = message.replace('+', ' ')
    app.logger.error("{}: {}".format(title, message))
    return render_error(title, message)


@app.route('/error')
def generate_error():
    """this just raises - use only for TEST purposes"""
    raise RuntimeError("this was an auto-generated error")


def get_all_queries():
    queries = []
    all_queries = snooper.parse_queries(conf.queries)
    for query_name, query_value in all_queries.iteritems():
        args = query_value.get('params', [])
        queries.append({query_name: args})
    return queries


def delete_query(query):
    queries = snooper.parse_queries(conf.queries)
    if not queries:
        raise ApiException('No queries found')
    elif query not in queries:
        raise ApiException('Query {} not found'.format(query))
    queries.pop(query)
    app.logger.debug('Query {} removed'.format(query))
    with open(conf.queries, 'w') as fd:
        json.dump({"queries": queries}, fd, sort_keys=True, indent=4, separators=(',', ': '))
    return json.dumps({'result': 'removed'})


def upsert_query(query, is_new=False):
    queries = snooper.parse_queries(conf.queries)
    if not queries:
        raise ApiException('No queries found')
    if is_new and query in queries:
        raise ApiException('Query {} already exists'.format(query))
    elif not is_new and query not in queries:
        raise ApiException('Query {} not found'.format(query))
    try:
        query_json = json.loads(request.data)
        if snooper.validate_query(query_json, queries):
            queries[query] = query_json
    except Exception as e:
        app.logger.error('Cannot parse data {} into valid JSON: {}'.format(request.data, e))
        raise ApiException(e)
    app.logger.debug('Query {} created/updated: {}'.format(query, queries[query]['sql']))
    with open(conf.queries, 'w') as fd:
        json.dump({"queries": queries}, fd, sort_keys=True, indent=4, separators=(',', ': '))
    return json.dumps({'result': 'success'})


def get(query, args=None):
    query_dict = snooper.parse_queries(conf.queries).get(query)
    if query_dict:
        params = None
        if args:
            params = snooper.parse_query_params(args.split('/'))
        res = run_query(query_dict.get("sql"), params)
        res["drill_down"] = query_dict.get("drill_down")
        return json.dumps(res)
    else:
        app.logger.error('Could not find query %s', query_dict)
        return redirect(url_for('/'.join(['error',
                        urllib.quote('Query Not Found'),
                        urllib.quote('Could not find query {} in the given query JSON file [{}]'
                                     .format(query_dict, conf.queries))])))


def run_query(query, params=None):
    db_conn.query = query
    db_conn.params = params
    app.logger.debug('Executing query: {} - with params: {}'.format(db_conn.query,
                                                                    db_conn.params))
    res = db_conn.execute()
    app.logger.debug('Found {} results'.format(res["rowcount"]))
    return res


class PromotionCodesResource(restful.Resource):
    REQUEST_ARGS = ['cloud', 'provider', 'cloud_type', 'created_by']

    def __init__(self):
        parser = reqparse.RequestParser()
        for arg in PromotionCodesResource.REQUEST_ARGS:
            parser.add_argument(arg, location='form')
        self._parser = parser

    @staticmethod
    def _check_args_exist_in_request(args):
        for required in PromotionCodesResource.REQUEST_ARGS:
            if not required in args:
                app.logger.error(
                    "Argument {} not found in the request arguments".format(required, ))
                return False
        return True

    def post(self, count):
        args = self._parser.parse_args()
        if not PromotionCodesResource._check_args_exist_in_request(args):
            app.logger.error("All required args should be passed in the request, "
                             "found: {}".format(args))
            return render_error('Missing Argument',
                                'All required args [{}] should be passed in the request, '
                                'only {} found'.format(PromotionCodesResource.REQUEST_ARGS, args))
        try:
            mgr = snooper.CouponsManager(args['provider'],
                                         args['cloud'],
                                         args['cloud_type'],
                                         args['created_by'], db=db_conn)
            filename = '/tmp/coupons.csv'
            mgr.make_coupons(count, filename=filename)
            return send_file(filename, as_attachment=True)
        except Exception as e:
            app.logger.error(e)
            return render_error("Error creating codes", e.message)


def render_error(title, message):
    """ Helper method to just render an error page
    """
    content_type = request.headers['Content-Type']
    if content_type == 'application/json':
        err = {
            'message': message,
            'title': title
        }
        return json.dumps(err)
    return render_template('err_msg.html', title=title, message=message)


def render_template(template, **kwargs):
    """ Helper method to return the given template

        This is needed due to the nefarious conflict between assumed defaults in Flask RESTful and
        Flask itself.
    """
    response = make_response(flask.render_template(template, **kwargs))
    response.headers["Content-type"] = "text/html"
    return response


def get_db():
    """ Connects to the database

        Helper method, creates the connection the first time, then caches it in Flask's ```g```

        @return: a DB connection, newly created if necessary
        @rtype: L{DbSnooper}
    """
    db = getattr(flask.g, '_database', None)
    if not db:
        conf = snooper.parse_args()
        flask.current_app._logger.info("Opening connection to DB: {}".format(conf.conf))
        db = snooper.DbSnooper(conf=snooper.config_connection(conf))
        flask.g._database = db
    return db


db_conn = LocalProxy(get_db)


def build_routes():
    """ Sets up the routes for the REST API.

        @param api: the Flask REST object to add routes to
        @type api: L{restful.Api}
    """
    api = restful.Api(app)
    PromotionCodesResource._conf = conf
    PromotionCodesResource._logger = app.logger
    api.add_resource(PromotionCodesResource, '/'.join(['', 'codes', '<int:count>']))


class ApiException(Exception):
    pass


def run_server():
    """ The main server app, starts up Flask, sets up the routes and handles requests
    """

    build_routes()
    app.run(debug=conf.debug, host='0.0.0.0')


if __name__ == '__main__':
    run_server()
