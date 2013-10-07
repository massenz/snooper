#!/usr/bin/env python
#
# Copyright (c) 2013 RiverMeadow Software Inc. All rights reserved.

__author__ = 'marco'

from flask import send_file
from flask.ext import restful
from flask.ext.restful import reqparse

import server
import snooper


class PromotionCodesResource(restful.Resource):
    REQUEST_ARGS = ['cloud', 'provider', 'cloud_type', 'created_by']

    _conf = server.conf
    _logger = server.app.logger

    def __init__(self):
        parser = reqparse.RequestParser()
        for arg in PromotionCodesResource.REQUEST_ARGS:
            parser.add_argument(arg, location='form')
        self._parser = parser

    @staticmethod
    def _check_args_exist_in_request(args):
        for required in PromotionCodesResource.REQUEST_ARGS:
            if not required in args:
                server.app.logger.error(
                    "Argument {} not found in the request arguments".format(required, ))
                return False
        return True

    def post(self, count):
        args = self._parser.parse_args()
        if not PromotionCodesResource._check_args_exist_in_request(args):
            self._logger.error("All required args should be passed in the request, "
                            "found: {}".format(args))
            return server.render_error('Missing Argument',
                                       'All required args [{}] should be passed in the request, '
                                       'only {} found'.format(PromotionCodesResource.REQUEST_ARGS,
                                                              args))
        try:
            mgr = snooper.CouponsManager(args['provider'],
                                         args['cloud'],
                                         args['cloud_type'],
                                         args['created_by'], db=server.db_conn)
            filename = '/tmp/coupons.csv'
            mgr.make_coupons(count, filename=filename)
            return send_file(filename, as_attachment=True)
        except Exception as e:
            self._logger.error(e)
            return server.render_error("Error creating codes", e.message)


def run_server(host='0.0.0.0', port=5001):
    api = restful.Api(server.app)
    api.add_resource(PromotionCodesResource, '/'.join(['', 'codes', '<int:count>']))
    server.app.run(debug=server.conf.debug, host=host, port=port)

if __name__ == '__main__':
    run_server()
