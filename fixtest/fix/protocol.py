""" FIX receiver class - responsible for the implementation
    of the FIX protocol.

    Copyright (c) 2014 Kenn Takara
    See LICENSE for details

"""

import datetime
import logging

from fixtest.fix.constants import FIX
from fixtest.fix.message import FIXMessage
from fixtest.fix.parser import FIXParser
from fixtest.fix.utils import format_time


class FIXDataError(ValueError):
    """ Exception: Problem found with the data in the message. """
    def __init__(self, refid, message):
        super(FIXDataError, self).__init__()
        self.reference_id = refid
        self.message = message

    def __str__(self):
        return self.message


class FIXTimeoutError(ValueError):
    """ Exception: Timeout. """
    def __init__(self, message):
        super(FIXTimeoutError, self).__init__()
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
            heartbeat: The heartbeat interval (in secs).  If set to 0,
                then no heartbeat processing is performed.  (Default:0)
            filter_heartbeat: If this is set to True, then heartbeat and
                TestRequest messages will not be passed on via
                on_message_received(). (Default: False)
            debug: Set this to True for debug logging.  (Default: False)
    """
    # pylint: disable=too-many-instance-attributes

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

        if len(self.link_config.get('protocol_version', '')) == 0:
            raise ValueError('link_config missing protocol_version')

        # heartbeat processing
        self.heartbeat = self.link_config.get('heartbeat', 0)
        self.filter_heartbeat = False
        self._testrequest_id = None
        self._testrequest_time = None

        # protocol state information
        self._send_seqno = self.link_config.get('send_seqno', 0)
        self._last_send_time = datetime.datetime.now()
        self._received_seqno = 0
        self._last_received_time = datetime.datetime.now()

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

    def prepare_send_message(self, message):
        """ Sends a message via the transport.
        """
        self._send_seqno += 1
        send_time = datetime.datetime.now()

        # update some of the required fields for sending
        message[8] = self.link_config['protocol_version']
        message[34] = self._send_seqno
        message[52] = format_time(send_time)

        # verify required tags
        for tag in self.link_config['required_fields']:
            # these two tags are updated when generating the binary
            if tag in {9, 10}:
                continue

            if tag not in message or len(str(message[tag])) == 0:
                raise FIXDataError(tag, 'missing field: id:{0}'.format(tag))

        self._last_send_time = send_time
        return message

    def on_message_received(self, message, message_length, checksum):
        """ This is the callback from the parser when a message has
            been received.
        """
        # verify required tags
        for tag in self.link_config['required_fields']:
            if tag not in message or len(str(message[tag])) == 0:
                raise FIXDataError(tag, 'missing field: id:{0}'.format(tag))

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
                9, 'length mismatch: expect:{0} received:{1}'.format(
                    message_length, int(message[9])))

        if checksum != int(message[10]):
            raise FIXDataError(
                10, 'checksum mismatch: expect:{0} received:{1}'.format(
                    checksum, message[10]))

        self._last_received_time = datetime.datetime.now()

        # Have we received our testrequest response?
        if (message.msg_type() == FIX.HEARTBEAT and
                message.get(112, '') == self._testrequest_id):
            self._testrequest_time = None
            self._testrequest_id = None

        # We have received a testrequest and need to send a response
        if message.msg_type() == FIX.TEST_REQUEST:
            self.transport.send_message(
                FIXMessage(source=[(35, FIX.HEARTBEAT),
                                   (112, message[112]),
                                   (49, self.link_config['sender_compid']),
                                   (56, self.link_config['target_compid'])]))

        if (not self.filter_heartbeat or
                (message.msg_type() not in {FIX.HEARTBEAT, FIX.TEST_REQUEST})):
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
        if self.heartbeat <= 0:
            return

        now = datetime.datetime.now()

        # Have we received a testrequest response before we timed out?
        if (self._testrequest_id is not None and
                (now - self._testrequest_time).seconds > 2*self.heartbeat):
            raise FIXTimeoutError('testrequest response timeout')

        # if heartbeat seconds have elapsed since the last time
        # a message was sent, send a heartbeat
        if (now - self._last_send_time).seconds > self.heartbeat:
            self.transport.send_message(
                FIXMessage(source=[(35, FIX.HEARTBEAT),
                                   (49, self.link_config['sender_compid']),
                                   (56, self.link_config['target_compid'])]))

        # if heartbeat seconds + "some transmission time" have elapsed
        # since a message was received, send a TestRequest
        if (now - self._last_received_time).seconds > self.heartbeat:
            testrequest_id = "TR{0}".format(format_time(now))
            self._testrequest_time = now
            self._testrequest_id = testrequest_id
            self.transport.send_message(
                FIXMessage(source=[(35, FIX.TEST_REQUEST),
                                   (112, testrequest_id),
                                   (49, self.link_config['sender_compid']),
                                   (56, self.link_config['target_compid'])]))
