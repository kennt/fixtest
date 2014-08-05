""" Simple client/server controller for testing.

    Copyright (c) 2014 Kenn Takara
    See LICENSE for details

"""

import logging
import time

from fixtest.base.controller import TestCaseController
from fixtest.base.queue import TestInterruptedError
from fixtest.base.utils import log_text
from fixtest.fix.transport import FIXTransportFactory


class LogonController(TestCaseController):
    """ The base class for FIX-based TestCaseControllers.

        This creates a client and a server that will 
        communicate with each other.  So they will use
        the same link config.
    """
    def __init__(self, **kwargs):
        super(LogonController, self).__init__(**kwargs)

        self.testcase_id = 'Simple-1'
        self.description = 'Test of the command-line tool'

        config = kwargs['config']

        self.server_config = config.get_role('test-server')
        self.server_config.update({'name': 'server-9940'})

        self.server_link_config = config.get_link('client', 'test-server')
        self.server_link_config.update({
            'sender_compid': self.server_link_config['test-server'],
            'target_compid': self.server_link_config['client'],
            })

        self.client_config = config.get_role('client')
        self.client_config.update({'name': 'client-9940'})

        self.client_link_config = config.get_link('client', 'test-server')
        self.client_link_config.update({
            'sender_compid': self.client_link_config['client'],
            'target_compid': self.client_link_config['test-server'],
            })

        self._servers = dict()
        self._clients = dict()

        factory = FIXTransportFactory('server-9940',
                                      self.server_config,
                                      self.server_link_config)
        server = {
            'name': 'server-9940',
            'port': self.server_link_config['port'],
            'factory': factory,
        }
        self._servers[server['name']] = server

        # In the client case we do not need to provide a
        # factory, Just need a transport.
        client = {
            'name': 'client-9940',
            'host': self.client_link_config['host'],
            'port': self.client_link_config['port'],
            'node': factory.create_transport('client-9940',
                                             self.client_config,
                                             self.client_link_config),
        }
        self._clients[client['name']] = client

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
        # at this point the servers should be waiting
        # so startup the clients
        self.wait_for_client_connections(20)

        # at this point the servers should be connected
        # also
        self.wait_for_server_connections(10)

    def teardown(self):
        pass

    def run(self):
        pass
