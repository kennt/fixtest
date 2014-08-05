""" FIX transport class - responsible for the interface
    between the protocol and the actual Twisted transport.

    Copyright (c) 2014 Kenn Takara
    See LICENSE for details

"""

import logging
from twisted import internet

from fixtest.base import ConnectionError
from fixtest.base.queue import MessageQueue
from fixtest.base.utils import log_text
from fixtest.fix.constants import FIX
from fixtest.fix.protocol import FIXProtocol
from fixtest.fix.utils import log_message


class FIXTransportFactory(internet.protocol.Factory):
    """ The factory interface for the FIX Transport.
    """
    def __init__(self, name, node_config, link_config):
        self.count = 0

        self._name = name
        self._node_config = node_config
        self._link_config = link_config

        self._servers = list()

        self._logger = logging.getLogger(__name__)

    def buildProtocol(self, addr):
        """ Creates and pulls together the components to
            build up the full interface.  This is called from
            Twisted.
        """
        # pylint: disable=unused-argument

        log_text(self._logger.info, None,
                 'Connected: {0} : {1}'.format(self.__class__, self._name))

        transport = self.create_transport(self._name,
                                          self._node_config,
                                          self._link_config)

        self._servers.append(transport)
        self.count += 1
        return transport

    def create_transport(self, name, node_config, link_config):
        """ Internal method used for creating a transport

            Mainly used to create client protocols.

            Arguments:
                name:

            Returns: an instance of a FIxTransport
        """
        # pylint: disable=no-self-use
        queue = MessageQueue(name)
        transport = FIXTransport(name, None, queue)
        protocol = FIXProtocol(name,
                               transport,
                               config=node_config,
                               link_config=link_config)
        transport.protocol = protocol
        return transport

    def cancel(self):
        """ Cancels the test.  This will forward the cancel to
            the servers created from this factory.
        """
        for server in self._servers:
            server.cancel()

    # Callbacks from Twisted upon server startup
    def server_success(self, result, *args, **kwargs):
        """ This is called when a server starts listening """
        # pylint: disable=unused-argument
        server = args[0]
        server['listener'] = result

        log_text(self._logger.info, __name__,
                 'server:{0} listening on port {1}'.format(server['name'],
                                                           server['port']))

    def server_failure(self, error, *args, **kwargs):
        """ This is called when a server fails to connect """
        # pylint: disable=unused-argument
        server = args[0]
        server['error'] = error
        log_text(self._logger.error, __name__,
                 'server:{0} failed to start: {1}'.format(args[0]['name'],
                                                          error))
        return ConnectionError(str(error))


class FIXTransport(internet.protocol.Protocol):
    """ This class is the interface between the FIXProtocol and
        the actual Twisted transport.
    """
    def __init__(self, name, protocol, queue):
        self.name = name
        self.protocol = protocol
        self.queue = queue

        self._logger = logging.getLogger(__name__)

    def connectionMade(self):
        log_text(self._logger.info, self.name, "Connection made")

    def connectionLost(self, reason=None):
        # pylint: disable=unused-argument
        log_text(self._logger.info, self.name, "Connection lost")

    def dataReceived(self, data):
        """ This is the callback from Twisted.
        """
        self.protocol.on_data_received(data)

    def on_message_received(self, message):
        """ This is the callback from the protocol.
        """
        log_message(self._logger.info, self.name, message, 'message received')

        # forward the message to the queue only if not a
        # heartbeat/testrequest
        if message.msg_type() not in {FIX.HEARTBEAT, FIX.TEST_REQUEST}:
            self.queue.add(message)

    def send_message(self, message):
        """ This is the callback from the protocol.  Send the
            message onto through the transport.
        """
        log_message(self._logger.info, self.name, message, 'message sent')

        if self.transport is not None:
            self.transport.send_message(message.to_binary())

    def cancel(self):
        """ Cancel any remaining operations.
        """
        self.queue.cancel()

    def wait_for_message(self, title='', timeout=10):
        """ Waits until a message has been received.

            Basically, this checks the queue until a message
            has been received.  The purpose of this is to
            provide a synchronous interface on an asynchronous
            interface.

            Arguments:
                title: This is used for logging, to indicate
                    what we are waiting for.
                timeout: The timeout in secs.  (Default: 10)

            Returns: A message

            Raises:
                fixtest.base.TestInterruptedError:
                fixtest.base.TimeoutError:
        """
        return self.queue.waitForMessage(title=title, timeout=timeout)

    def client_success(self, result, *args, **kwargs):
        """ This is called from Twisted upon connection """
        # pylint: disable=unused-argument
        client = args[0]
        client['connected'] = 'success'
        log_text(self._logger.info, __name__,
                 'client:{0} connected to {1}:{2}'.format(client['name'],
                                                          client['host'],
                                                          client['port']))

    def client_failure(self, error, *args, **kwargs):
        """ This is called from Twisted upon an error """
        # pylint: disable=unused-argument
        client = args[0]
        client['error'] = error
        log_text(self._logger.error, __name__,
                 'client:{0} failed to start: {1}'.format(args[0]['name'],
                                                          error))
        return ConnectionError(str(error))
