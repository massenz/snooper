__author__ = 'marco'

import unittest

import snooper
import server


class ServerTest(unittest.TestCase):

    def test_build_from(self):
        expected = '/'.join([server.REST_BASE_URL, 'query', '<query>'])
        self.assertEqual(expected, server.build_from('query', '<query>'))


