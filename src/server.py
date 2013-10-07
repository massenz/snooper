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
from flask import (Flask,
                   abort,
                   redirect,
                   make_response,
                   request, url_for)
import json
import logging
import snooper
import urllib
from werkzeug.local import LocalProxy


SECRET_KEY = '#3K5h43Hl53&s0Bod62y$%C34t6oDv3NN47Oz24GT7$3TFJWDS5yX7E7&a4994e0'
REST_BASE_URL = '/api/1'


class ApiException(Exception):
    pass


conf = snooper.parse_args()
app = Flask('snooper')
if not conf.debug:
    # By default, in non-debug mode, the app logger does not log anything
    # we enable it here to log DEBUG level to Console
    app.logger.setLevel(logging.DEBUG)
    app.logger.addHandler(logging.StreamHandler())


# TODO: understand why this cannot be a @staticmethod inside Routes - Python doesn't like it
def build_from(*args):
        """ Builds a `default` route from a list of path segments

            Usage: build_from('query', '<query>') will build '/api/1/query/<query>'
                assuming ``REST_BASE_URL`` is defined as '/api/1'

        @param args: a sequence of segments to build the route from
        @type args: sequence
        @return: a full API route (eg '/api/1/query/<query>')
        @rtype: string
        """
        base = [REST_BASE_URL]
        base.extend(args)
        return '/'.join(base)


class Routes(object):
    """ A single place where to put all the routes for the Flask framework

        I still have issues with the way Flask handles routes (IMO JAX-RS does a much better job
        of keeping the routes separated) but at least we can keep them there in one place.
    """
    TEST = build_from('test')
    QUERY_ALL = build_from('query')
    QUERY = build_from('query', '<query>')
    QUERY_WITH_ARGS = build_from('query', '<query>', '<path:args>')
    ERROR = build_from('error', '<title>', '<message>')
    INFO = build_from('info')
    INFO_QUERY = build_from('info', '<query>')


@app.errorhandler(404)
def redirect_to_ui(error):
    return render_template('index.html')


@app.errorhandler(Exception)
def handle_ex(exception):
    # TODO: have a separate exception log
    app.logger.exception(exception)
    return render_error('Application Error', str(exception))


@app.route(Routes.TEST)
def test():
    """Used to test correct re-routing of application exceptions"""
    raise RuntimeError("this was an error")


@app.route(Routes.QUERY_ALL)
def get_all():
    """ Gets all existing queries names

        @return: a list of all queries in the "queries" key:
            {"queries": [ "get_user", "get_migrations", .... ]}
        @rtype: string
    """
    all_queries = snooper.parse_queries(conf.queries)
    queries = []
    for query in all_queries:
        queries.append(query)
    return json.dumps({"queries": queries})


@app.route(Routes.QUERY_WITH_ARGS)
@app.route(Routes.QUERY, methods=['GET', 'POST', 'PUT', 'DELETE'])
def query_resource(query, args=None):
    if request.method in ['POST', 'PUT']:
        return upsert_query(query, is_new=(request.method == 'POST'))
    elif request.method == 'GET':
        return get(query, args)
    elif request.method == 'DELETE':
        return delete_query(query)
    else:
        return ApiException('Method {} not implemented'.format(request.method))


@app.route(Routes.ERROR, methods=['POST'])
def post_error_message(title, message):
    title = title.replace('+', ' ')
    message = message.replace('+', ' ')
    app.logger.error("{}: {}".format(title, message))
    return render_error(title, message)


@app.route('/error')
def generate_error():
    """this just raises - use only for TEST purposes"""
    raise RuntimeError("this was an auto-generated error")


@app.route(Routes.INFO_QUERY)
def get_query_info(query):
    """Returns all info about a query """
    queries = snooper.parse_queries(conf.queries)
    if not queries:
        raise ApiException('No queries found')
    elif query not in queries:
        abort(404)
    result = queries.get(query)
    result['name'] = query
    return json.dumps(result)

@app.route(Routes.INFO)
def get_all_queries():
    all_queries = snooper.parse_queries(conf.queries)
    queries = []
    for name, query in all_queries.iteritems():
        query['name'] = name
        queries.append(query)
    return json.dumps(queries)


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
    # TODO: return a 205 RESET CONTENT instead
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
    # TODO: return a 201 CREATED code instead or 200 OK (for a PUT)
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


def render_error(title, message):
    """ Helper method to just render an error page
    """
    content_type = request.headers['Content-Type']
    if content_type == 'application/json':
        err = {
            'error': {
                'message': message,
                'title': title
            }
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
        _conf = snooper.parse_args()
        flask.current_app.logger.info("Opening connection to DB: {}".format(_conf.conf))
        db = snooper.DbSnooper(conf=snooper.config_connection(conf))
        flask.g._database = db
    return db


db_conn = LocalProxy(get_db)


def run_server(host='0.0.0.0', port=5000):
    app.run(debug=conf.debug, host=host, port=port)

if __name__ == '__main__':
    run_server()
