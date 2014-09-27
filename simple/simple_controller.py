""" Simple controller used for testing.

    Copyright (c) 2014 Kenn Takara
    See LICENSE for details

"""

import logging

from fixtest.base.controller import TestCaseController
from fixtest.fix.transport import FIXTransportFactory


class SimpleController(TestCaseController):
    """ The base class for FIX-based TestCaseControllers.
    """
    def __init__(self, **kwargs):
        super(SimpleController, self).__init__(**kwargs)

        self.testcase_id = 'Simple-1'
        self.description = 'Test of the command-line tool'

        config = kwargs['config']

        self.node_config = config.get_role('test-server')
        self.node_config.update({'name': 'server-9940'})

        self.link_config = config.get_link('client', 'test-server')
        self.link_config.update({
            'sender_compid': self.link_config['test-server'],
            'target_compid': self.link_config['client'],
            })

        self._servers = dict()
        self._clients = dict()

        server = {
            'name': 'server-9940',
            'port': 9940,
            'factory': FIXTransportFactory('server-9940',
                                           self.node_config,
                                           self.link_config),
        }
        self._servers[server['name']] = server

        self._logger = logging.getLogger(__name__)

    def clients(self):
        """ The clients that need to be started """
        return self._clients

    def servers(self):
        """ The servers that need to be started """
        return self._servers

    def setup(self):
        """ For this case, wait until our servers are all
            connected before continuing with the test.
        """
        # Have to wait for a server connection before we
        # can run the test
        self.wait_for_server_connections(10)

    def teardown(self):
        pass

    def run(self):
        pass
