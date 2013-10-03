__author__ = 'marco'


import unittest

import snooper


class SnooperTest(unittest.TestCase):

    def test_syntax(self):
        query = {
            "drill_down": {
                "email_address": "/api/1/query/get_user_by_email/email/$"
            },
            "params": [
                {
                    "label": "User UUID",
                    "name": "id"
                }
            ],
            "sql": "SELECT * FROM USERS WHERE UUID=%(id)s"
        }
        queries = {}
        res = snooper.validate_query(query, queries)
        self.assertTrue(res)

    def test_syntax_3(self):
        query = {
            "drill_down": {
                "email_address": "/api/1/query/get_user_by_email/email/$"
            },
            "params": [
                {
                    "label": "User UUID",
                    "name": "id"
                },
                {
                    "label": "first",
                    "name": "first_name"
                },
                {
                    "label": "last",
                    "name": "last_name"
                }

            ],
            "sql": "SELECT * FROM USERS WHERE UUID=%(id)s AND first_name = %(first_name)s "
                   "OR last_name = %(last_name)s"
        }
        queries = {}
        res = snooper.validate_query(query, queries)
        self.assertTrue(res)

    def test_invalid_syntax(self):
        query = {
            "drill_down": {
                "email_address": "/api/1/query/get_user_by_email/email/$"
            },
            "params": [
                {
                    "label": "User UUID",
                    "name": "foo"
                }
            ],
            "sql": "SELECT * FROM USERS WHERE UUID=%(baz)s"
        }
        queries = {}
        with self.assertRaises(SyntaxError):
            snooper.validate_query(query, queries)

    def test_me(self):
        print 'boooo'
        q = {
            "sql": "SELECT * FROM USERS WHERE UUID=%(id)s AND first_name=%(name)s",
            "drill_down": {
                "email_address": "/api/1/query/get_user_by_email/email/$"
            },
            "params": [{
                "label": "User UUID",
                "name": "id"
            }]
        }
        qs = {}
        self.assertRaises(SyntaxError, snooper.validate_query(q, qs))
