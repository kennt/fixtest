""" Simple client/server controller for testing.

    Copyright (c) 2014 Kenn Takara
    See LICENSE for details

"""

import logging

from fixtest.base.asserts import *
from fixtest.base.controller import TestCaseController
from fixtest.fix.constants import FIX
from fixtest.fix.messages import logon_message, logout_message
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
        factory.filter_heartbeat = False

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
        self.wait_for_client_connections(10)
        self.wait_for_server_connections(10)

    def teardown(self):
        pass

    def run(self):
        """ This test is a demonstration of logon and
            heartbeat/TestRequest processing.  Usually
            the logon process should be done from setup().
        """
        client = self._clients['client-9940']['node']
        client.protocol.heartbeat = 5
        # We only have a single server connection
        server = self._servers['server-9940']['factory'].servers[0]
        server.protocol.heartbeat = 5

        # client -> server
        client.send_message(logon_message(client))

        # server <- client
        message = server.wait_for_message(title='waiting for logon')
        assert_is_not_none(message)
        assert_tag(message, [(35, FIX.LOGON)])

        # server -> client
        server.send_message(logon_message(server))
        server.start_heartbeat(True)

        # client <- server
        message = client.wait_for_message(title='waiting for logon ack')
        client.start_heartbeat(True)
        assert_is_not_none(message)
        assert_tag(message, [(35, FIX.LOGON)])

        # Logout
        client.send_message(logout_message(client))
        message = server.wait_for_message(title='waiting for logout')
        assert_is_not_none(message)
        assert_tag(message, [(35, FIX.LOGOUT)])

        server.send_message(logout_message(server))
        server.start_heartbeat(False)

        message = client.wait_for_message('waiting for logout ack')
        client.start_heartbeat(False)
        assert_is_not_none(message)
        assert_tag(message, [(35, FIX.LOGOUT)])
