""" FIX receiver class - responsible for the implementation
    of the FIX protocol.

    Copyright (c) 2014 Kenn Takara
    See LICENSE for details

"""

import logging
from twisted.internet import protocol, reactor

from base.utils import log_text
from fix.parser import FIXParser


class FIXProtocol(protocol.Protocol):
    """ Implements the transport interface.  Instead of dealing directly
        with byte streams, we now deal with Messages.  This layer is
        also responsible for hiding some of the lower level details, such
        as Heartbeat/TestRequest processing.

        Attributes:
                name: A descriptive name given to this connection.
                parser: References an implementation for the parser.
                queue: This is the message queue associated with this
                    connection.
                config: A dict() for the endpoint configuration.
                link_config: A dict for the link configuration.
                    protocol_version:  This is the FIX version that is
                        sent and is expected in the BeginString(8).
                    sender_compid: The sender endpoint ID.
                    target_compid: The target endpoint ID.
                    heartbeat: The heartbeat interval (in secs).  IF this
                        is set to -1, then the heartbeat is not sent.
                    send_msg_seqno: This is the starting seqno.
                    orderid_no: This is the starting order no.
                debug: Set this to True for debug logging.  (Default: False)
    """
    def __init__(self, name, queue, **kwargs):
        """ FIXProtocol initialization

            Args:
                name: A descriptive name given to this connection.
                queue: This is the message queue associated with this
                    connection.
                config: A dict() for the endpoint configuration.
                link_config: A dict for the link configuration.
                    protocol_version:  This is the FIX version that is
                        sent and is expected in the BeginString(8).
                    sender_compid: The sender endpoint ID.
                    target_compid: The target endpoint ID.
                    heartbeat: The heartbeat interval (in secs).  IF this
                        is set to -1, then the heartbeat is not sent.
                    send_msg_seqno: This is the starting seqno.
                    orderid_no: This is the starting order no.
                    binary_fields: The list of FIX binary fields supported
                        or needed by this link (Default: None).
                        Note that binary fields come in pairs.  The first
                        field contains the length of the data and the second
                        field contains the actual data.  The convention is that
                        the IDs are sequential.  For example, if the length
                        field is tag 123, then tag 124 contains the data.
                        Note that only the first field should be included
                        in this list.
                    group_fields: The list of FIX binary fields supported
                        or needed by this link (Default: None).
                    max_length: The maximum length of message (Default: 2048)
                debug: Set this to True for debug logging.  (Default: False)

            Raises:
                ValueError: name and queue are required parameters.
        """
        if name is None:
            raise ValueError("name is None")
        if queue is None:
            raise ValueError("queue is None")

        self.name = name
        self.queue = queue
        self.config = kwargs.get('config', dict())
        self.link_config = kwargs.get('link_config', dict())
        self._debug = kwargs.get('debug')

        self.parser = FIXParser(self.on_message_received,
                                self.on_error_received,
                                binary_fields=self.link_config.get(
                                    'binary_fields', None),
                                group_fields=self.link_config.get(
                                    'group_fields', None),
                                max_length=self.link_config.get(
                                    'max_length', 2048))

        self._logger = logging.getLogger(__name__)

    def dataReceived(self, data):
        """ This is the callback that is called from Twisted.
        """
        self.parser.on_data_received(data)

    def send_message(self, message):
        """ Sends a message via the transport.
        """
        if self.transport:
            reactor.callFromThread(self.transport.write, message.to_binary())
        else:
            log_text(self._logger.info, None,
                     'Cannot send message, no transport')

    def on_message_received(self, message):
        """ This is the callback from the parser when a message has
            been received.
        """

    def on_error_received(self, error):
        """ This is the callback from the parser when an error in the
            message has been detected.
        """

    def on_timer_tick_received(self):
        """ This is the Twisted timer callback when the heartbeat interval
            has elapsed.
        """
