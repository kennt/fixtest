""" FIX transport class - responsible for the interface
    between the protocol and the actual Twisted transport.

    Copyright (c) 2014 Kenn Takara
    See LICENSE for details

"""

import logging
from twisted import internet

from fixtest.fix.constants import FIX
from fixtest.fix.utils import log_message


class FIXTransport(internet.protocol.Protocol):
    """ This class is the interface between the FIXProtocol and
        the actual Twisted transport.
    """
    def __init__(self, name, protocol):
        self.name = name
        self.protocol = protocol
        self.queue = None

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
            self.queue.append(message)

    def send_message(self, message):
        """ This is the callback from the protocol.  Send the
            message onto through the transport.
        """
        log_message(self._logger.info, self.name, message, 'message sent')

        if self.transport is not None:
            self.transport.send_message(message.to_binary())
