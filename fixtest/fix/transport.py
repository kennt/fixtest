""" FIX transport class - responsible for the interface
    between the protocol and the actual Twisted transport.

    Copyright (c) 2014 Kenn Takara
    See LICENSE for details

"""

import logging
from twisted import internet

from fixtest.base.queue import MessageQueue
from fixtest.fix.constants import FIX
from fixtest.fix.protocol import FIXProtocol
from fixtest.fix.utils import log_message


class FIXTransportFactory(internet.protocol.Factory):
    """ The factory interface for the FIX Transport.
    """
    def __init__(self, name, node_config, link_config):
        self._name = name
        self._node_config = node_config
        self._link_config = link_config

    def buildProtocol(self, addr):
        """ Creates and pulls together the components to
            build up the full interface.
        """
        # pylint: disable=unused-argument

        queue = MessageQueue(self._name)
        transport = FIXTransport(self._name, None, queue)
        protocol = FIXProtocol(self._name,
                               transport,
                               config=self._node_config,
                               link_config=self._link_config)
        transport.protocol = protocol
        return transport


class FIXTransport(internet.protocol.Protocol):
    """ This class is the interface between the FIXProtocol and
        the actual Twisted transport.
    """
    def __init__(self, name, protocol, queue):
        self.name = name
        self.protocol = protocol
        self.queue = queue

        self._logger = logging.getLogger(__name__)

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
                fixtest.base.queue.TestInterruptedError:
                fixtest.base.queue.TimeoutError:
        """
        return self.queue.waitForMessage(title=title, timeout=timeout)
