""" FIX receiver class - responsible for the implementation
    of the FIX protocol.

    Copyright (c) 2014 Kenn Takara
    See LICENSE for details

"""

import logging

# from base.utils import log_text
from ..fix.parser import FIXParser


class FIXDataError(ValueError):
    """ Exception: Problem found with the data in the message. """
    def __init__(self, refid, message):
        super(FIXDataError, self).__init__()
        self.reference_id = refid
        self.message = message

    def __str__(self):
        return self.message


class FIXProtocol(object):
    """ Implements the protocol interface.  Instead of dealing directly
        with byte streams, we now deal with Messages.  This layer is
        responsible for most of the administration level logic, such as
        handling of heartbeats/TestRequests.  This class will also
        handle tracking of certain appliction counters, such as
        message sequence numbers.

        Attributes:
                name: A descriptive name given to this connection.
                transport: The transport interface for this connection.
                config: A dict() for the endpoint configuration.
                    See the ROLES section in sample_config.py for examples.
                link_config: A dict for the link configuration.
                    See the CONNECTIONS section in sample_config.py for
                    examples and documentation.
                debug: Set this to True for debug logging.  (Default: False)
    """
    def __init__(self, name, transport, **kwargs):
        """ FIXProtocol initialization

            Args:
                name: A descriptive name given to this connection.
                transport: The transport used to interface with the
                    networking layer.
                config: A dict() for the endpoint configuration.
                    See the ROLES section in sample_config.py for examples.
                link_config: A dict for the link configuration.
                    See the CONNECTIONS section in sample_config.py for
                    examples and documentation.
                debug: Set this to True for debug logging.  (Default: False)

            Raises:
                ValueError: name and queue are required parameters.
        """
        if name is None:
            raise ValueError("name is None")
        if transport is None:
            raise ValueError("name is None")

        self.name = name
        self.transport = transport
        self.config = kwargs.get('config', dict())
        self.link_config = kwargs.get('link_config', dict())
        self._debug = kwargs.get('debug')

        self._parser = FIXParser(self,
                                 header_fields=self.link_config.get(
                                     'header_fields', None),
                                 binary_fields=self.link_config.get(
                                     'binary_fields', None),
                                 group_fields=self.link_config.get(
                                     'group_fields', None),
                                 max_length=self.link_config.get(
                                     'max_length', 2048))

        self._logger = logging.getLogger(__name__)

    def on_data_received(self, data):
        """ This is the notification from the transport.
        """
        # pass this onto the parser
        self._parser.on_data_received(data)

    def send_message(self, message):
        """ Sends a message via the transport.
        """
        # add whatever fields are needed
        self.transport.send_message(message.to_binary())

    def on_message_received(self, message, message_length, checksum):
        """ This is the callback from the parser when a message has
            been received.
        """
        # do whatever filtering we need to do here

        # verify required tags

        # verify the protocol version
        if 'protocol_version' in self.link_config:
            if self.link_config['protocol_version'] != message[8]:
                raise FIXDataError(
                    8, 'version mismatch: expect:{0} received:{1}'.format(
                        self.link_config['protocol_version'],
                        message[8]
                        ))

        # verify the length and checksum
        if message_length != int(message[9]):
            raise FIXDataError(
                9, 'length mismatch: expect:{0} received {1}'.format(
                    message_length, int(message[9])))

        if checksum != int(message[10]):
            raise FIXDataError(
                10, 'checksum mismatch: expect:{0} received {1}'.format(
                    checksum, message[10]))

        self.transport.on_message_received(message)

    def on_error_received(self, error):
        """ This is the callback from the parser when an error in the
            message has been detected.
        """
        # pylint: disable=no-self-use
        raise error

    def on_timer_tick_received(self):
        """ This is the Twisted timer callback when the heartbeat interval
            has elapsed.
        """
