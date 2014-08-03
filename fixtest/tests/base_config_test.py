""" base.config unit tests

    Copyright (c) 2014 Kenn Takara
    See LICENSE for details

"""

import os
import unittest

from fixtest.base.config import FileConfig, DictConfig


class TestConfig(unittest.TestCase):
    # pylint: disable=missing-docstring

    def setUp(self):
        self.config = DictConfig({
            'ROLES': {
                'clientX': {
                    'admin-port': 19000,
                    'admin-address': 'localhost',
                },
                'serverY': {
                    'admin-port': 19001,
                    'admin-address': 'localhost',
                }
            },
            'CONNECTIONS': [
                {
                    'name': 'client-fix-server',
                    'protocol': 'FIX',
                    'host': 'localhost',
                    'port': 8080,

                    # These are role:name
                    'clientX': 'client1',
                    'serverY': 'server1',

                    # This is which role has the role of the server
                    'acts-as-server': 'serverY',
                }
            ],
            'OTHER': {
                'test-id': 'hello'
            },
        })

    def test_get_role(self):
        role_config = self.config.get_role('serverY')
        self.assertIsNotNone(role_config)
        self.assertEquals(19001, role_config['admin-port'])

        self.assertRaises(KeyError, self.config.get_role, 'serverYYY')

    def test_get_link(self):
        link_config = self.config.get_link('clientX', 'serverY')
        self.assertIsNotNone(link_config)
        self.assertEquals('client-fix-server', link_config['name'])

        self.assertRaises(KeyError, self.config.get_link,
                          'clientX', 'server')
        self.assertRaises(KeyError, self.config.get_link,
                          'clientX', 'serverY', 'fix')
        self.assertRaises(KeyError, self.config.get_link,
                          'client', 'serverY')

    def test_get_section(self):
        other_config = self.config.get_section('OTHER')
        self.assertIsNotNone(other_config)
        self.assertEquals('hello', other_config['test-id'])

        self.assertRaises(KeyError, self.config.get_section,
                          'OTHERXX')


class TestFileConfig(unittest.TestCase):
    # pylint: disable=missing-docstring
    def test_fileconfig(self):
        file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                 'test_config.txt')
        config = FileConfig(file_path)
        self.assertIsNotNone(config)
        role_config = config.get_role('exchange')
        self.assertIsNotNone(role_config)
        self.assertEquals(19404, role_config['admin-port'])

        link_config = config.get_link('client', 'gateway', 'FIX')
        self.assertIsNotNone(link_config)
        self.assertEquals('client-FIX-gateway', link_config['name'])
