""" FIX transport class - responsible for the interface
    between the protocol and the actual Twisted transport.

    Copyright (c) 2014 Kenn Takara
    See LICENSE for details

"""

import datetime
import logging

from twisted import internet
from twisted.internet import task, reactor

from fixtest.base import ConnectionError
from fixtest.base.queue import MessageQueue
from fixtest.base.utils import log_text
from fixtest.fix.constants import FIX
from fixtest.fix.protocol import FIXProtocol
from fixtest.fix.utils import log_message


class FIXTransportFactory(internet.protocol.Factory):
    """ The factory interface for the FIX Transport.

        Attributes:
            servers: The list of server instances that
                this factory has created.
            filter_heartbeat: Set this to True to filter out
                heartbeat/TestRequest messages from instances
                created from this factory. (Default: True)
    """
    def __init__(self, name, node_config, link_config):
        self.count = 0

        self._name = name
        self._node_config = node_config
        self._link_config = link_config

        self.servers = list()
        self.filter_heartbeat = True

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

        self.servers.append(transport)
        return transport

    def create_transport(self, name, node_config, link_config):
        """ Internal method used for creating a transport

            Mainly used to create client protocols.

            Arguments:
                name:
                node_config:
                link_config:

            Returns: an instance of a FIxTransport
        """
        # pylint: disable=no-self-use
        transport = FIXTransport(name, link_config)
        protocol = FIXProtocol(name,
                               transport,
                               config=node_config,
                               link_config=link_config)
        protocol.filter_heartbeat = self.filter_heartbeat
        transport.protocol = protocol
        return transport

    def cancel(self):
        """ Cancels the test.  This will forward the cancel to
            the servers created from this factory.
        """
        for server in self.servers:
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

        Attributes:
            name: The descriptive name for the connection.
                Used mainly when logging.
            protocol: The protocol object that does the
                decoding of messages.
            queue: The queue used to read messages from.
            lc_task: The Twisted looping call task.
            sender_compid:
            target_compid:
    """
    # pylint: disable=too-many-instance-attributes

    def __init__(self, name, link_config):
        self.name = name
        self.protocol = None
        self.queue = MessageQueue(name)
        self.lc_task = None
        self.sender_compid = link_config['sender_compid']
        self.target_compid = link_config['target_compid']
        self._orderid_no = 0

        self._logger = logging.getLogger(__name__)

    def get_next_orderid(self):
        """ Generates a valid orderID.
            This uses a combination of the transport name,
            the current date, and an internal counter.

            Returns: a new orderID string
        """
        self._orderid_no += 1
        return "{0}/{1}/{2}".format(
            self.name,
            datetime.datetime.now().strftime("%Y%m%d"),
            self._orderid_no)

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
        self.protocol.prepare_send_message(message)
        data = message.to_binary()
        log_message(self._logger.info, self.name, message, 'message sent')

        if self.transport is not None:
            reactor.callFromThread(self.transport.write, data)

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
        return self.queue.wait_for_message(title=title, timeout=timeout)

    def start_heartbeat(self, enable):
        """ Starts/stops the hearbeat processing.

            Basically starts/stops a Twisted timer callback loop.
            Note that if the loop is already started calling
            start_heartbeat(True) will not do anything.  To change
            the heartbeat interval, it is necessary to call
            start_heartbeat(False) followed by start_heartbeat(True).

            Arguments:
                enable: True if starting the heartbeat processing,
                    False to stop the processing.
        """
        if enable:
            if self.lc_task is None:
                self.lc_task = task.LoopingCall(self.on_timer_tick_received)
                reactor.callFromThread(self.lc_task.start,
                                       self.protocol.heartbeat,
                                       now=False)
        else:
            if self.lc_task is not None:
                self.lc_task.stop()
                self.lc_task = None

    def on_timer_tick_received(self):
        """ This is the timer callback received from Twisted.
            Forwards this call onto the protocol.
        """
        self.protocol.on_timer_tick_received()

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
