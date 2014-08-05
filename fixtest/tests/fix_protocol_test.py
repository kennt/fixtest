""" fix.protocol unit tests

    Copyright (c) 2014 Kenn Takara
    See LICENSE for details

"""

import datetime
import unittest

from fixtest.fix.constants import FIX
from fixtest.fix.message import FIXMessage
from fixtest.fix.protocol import FIXProtocol, FIXDataError, FIXTimeoutError
from fixtest.fix.utils import flatten
from fixtest.tests.utils import to_fix

# pylint: disable=too-many-public-methods
# pylint: disable=missing-docstring


class TestFIXProtocol(unittest.TestCase):

    class MockFIXTransport(object):
        def __init__(self):
            self.protocol = None
            self.message_received_count = 0
            self.last_message_received = None

            self.message_sent_count = 0
            self.last_message_sent = None

            self.timeout_received_count = 0

        def on_message_received(self, message):
            self.message_received_count += 1
            self.last_message_received = message

        def send_message(self, message):
            self.protocol.prepare_send_message(message)
            self.message_sent_count += 1
            self.last_message_sent = message

        def on_timeout_received(self, text):
            # pylint: disable=unused-argument
            self.timeout_received_count += 1

    def __init__(self, *args, **kwargs):
        super(TestFIXProtocol, self).__init__(*args, **kwargs)

        self.protocol = None
        self.transport = None

    def setUp(self):
        # setup the protocol, standard FIX
        self.transport = TestFIXProtocol.MockFIXTransport()
        self.protocol = FIXProtocol('Test transport',
                                    self.transport,
                                    link_config={
                                        'protocol_version': 'FIX.4.2',
                                        'required_fields': [8, 9, 35],
                                        'header_fields': [8, 9, 35],
                                        'binary_fields': [],
                                        'group_fields': {},
                                        'sender_compid': 'sender',
                                        'target_compid': 'target',
                                    })
        self.transport.protocol = self.protocol

    def test_bad_protocol_version(self):
        """ Send a bad protocol_version through the protocol. """
        with self.assertRaises(FIXDataError) as context:
            self.protocol.on_data_received(to_fix('8=FIX.X.X',
                                                  '9=25',
                                                  '35=A',
                                                  '49=server',
                                                  '56=client',
                                                  '10=152'))
        self.assertEquals(8, context.exception.reference_id)

    def test_bad_length(self):
        """ Send a message with an incorrect length field (9). """
        with self.assertRaises(FIXDataError) as context:
            self.protocol.on_data_received(to_fix('8=FIX.4.2',
                                                  '9=999',
                                                  '35=A',
                                                  '49=server',
                                                  '56=client',
                                                  '10=000'))
        self.assertEquals(9, context.exception.reference_id)

    def test_bad_checksum(self):
        """ Send a message with an incorrect checksum field (10). """
        with self.assertRaises(FIXDataError) as context:
            self.protocol.on_data_received(to_fix('8=FIX.4.2',
                                                  '9=25',
                                                  '35=A',
                                                  '49=server',
                                                  '56=client',
                                                  '10=000'))
        self.assertEquals(10, context.exception.reference_id)

    def test_missing_required_fields(self):
        """ Test for missing required fields """
        with self.assertRaises(FIXDataError) as context:
            self.protocol.on_data_received(to_fix('8=FIX.4.2',
                                                  '9=5',
                                                  '49=s',
                                                  '10=233'))
        self.assertEquals(35, context.exception.reference_id)

    def test_header_fields_in_order(self):
        """ Test for out-of-order header fields """
        self.protocol.on_data_received(to_fix('8=FIX.4.2',
                                              '9=10',
                                              '49=s',
                                              '35=A',
                                              '10=252'))
        self.assertIsNotNone(self.transport.last_message_received)
        items = flatten(self.transport.last_message_received)

        # the order should be restored because the header fields will
        # have been pre-added.
        self.assertEquals(5, len(items))
        self.assertEquals(8, items[0][0])
        self.assertEquals(9, items[1][0])
        self.assertEquals(35, items[2][0])
        self.assertEquals(49, items[3][0])
        self.assertEquals(10, items[4][0])

    def test_send_heartbeat(self):
        """ Test heartbeat sending """
        now = datetime.datetime.now() - datetime.timedelta(seconds=1)
        self.protocol._last_send_time = now - datetime.timedelta(minutes=1)
        self.protocol._last_received_time = now
        last_time = self.protocol._last_send_time

        # start heartbeat processing
        self.protocol.heartbeat = 5     # time in secs
        self.protocol.filter_heartbeat = False

        self.assertEquals(0, self.transport.message_sent_count)

        self.protocol.on_timer_tick_received()

        self.assertEquals(1, self.transport.message_sent_count)
        message = self.transport.last_message_sent
        self.assertIsNotNone(message)
        self.assertEquals(FIX.HEARTBEAT, message.msg_type())
        self.assertNotEquals(last_time, self.protocol._last_send_time)

    def test_receive_heartbeat(self):
        """ Test receiving heartbeat """
        now = datetime.datetime.now() - datetime.timedelta(seconds=2)
        self.protocol._last_send_time = now
        self.protocol._last_received_time = now
        last_time = self.protocol._last_received_time

        self.protocol.filter_heartbeat = False

        self.protocol.on_data_received(to_fix('8=FIX.4.2',
                                              '9=5',
                                              '35=0',
                                              '10=161'))
        self.assertEquals(1, self.transport.message_received_count)
        self.assertNotEquals(last_time, self.protocol._last_received_time)

    def test_filter_heartbeat(self):
        """ Test heartbeat filtering """
        now = datetime.datetime.now() - datetime.timedelta(seconds=1)
        self.protocol._last_send_time = now - datetime.timedelta(minutes=1)
        self.protocol._last_received_time = now
        last_time = self.protocol._last_received_time

        # start heartbeat processing
        self.protocol.heartbeat = 5     # time in secs
        self.protocol.filter_heartbeat = True

        self.protocol.on_data_received(to_fix('8=FIX.4.2',
                                              '9=5',
                                              '35=0',
                                              '10=161'))

        self.assertEquals(0, self.transport.message_received_count)
        self.assertNotEquals(last_time, self.protocol._last_received_time)

    def test_send_testrequest(self):
        """ TestRequest sending """
        now = datetime.datetime.now() - datetime.timedelta(seconds=1)
        self.protocol._last_received_time = now - datetime.timedelta(minutes=1)
        self.protocol._last_send_time = now
        last_time = self.protocol._last_send_time

        # start heartbeat processing
        self.protocol.heartbeat = 5     # time in secs
        self.protocol.filter_heartbeat = False

        self.assertEquals(0, self.transport.message_sent_count)

        self.protocol.on_timer_tick_received()

        self.assertEquals(1, self.transport.message_sent_count)
        message = self.transport.last_message_sent
        self.assertIsNotNone(message)
        self.assertEquals(FIX.TEST_REQUEST, message.msg_type())
        self.assertNotEquals(last_time, self.protocol._last_send_time)

    def test_receive_testrequest(self):
        """ Test receiving testrequest """
        now = datetime.datetime.now() - datetime.timedelta(seconds=2)
        self.protocol._last_send_time = now
        self.protocol._last_received_time = now
        last_time = self.protocol._last_received_time

        self.protocol.filter_heartbeat = False

        self.protocol.on_data_received(to_fix('8=FIX.4.2',
                                              '9=13',
                                              '35=1',
                                              '112=tr1',
                                              '10=186'))
        self.assertEquals(1, self.transport.message_received_count)
        self.assertNotEquals(last_time, self.protocol._last_received_time)

    def test_filter_testrequest(self):
        """ Test testrequest filtering """
        now = datetime.datetime.now() - datetime.timedelta(seconds=1)
        self.protocol._last_send_time = now - datetime.timedelta(minutes=1)
        self.protocol._last_received_time = now
        last_time = self.protocol._last_received_time

        # start heartbeat processing
        self.protocol.heartbeat = 5     # time in secs
        self.protocol.filter_heartbeat = True

        self.protocol.on_data_received(to_fix('8=FIX.4.2',
                                              '9=13',
                                              '35=1',
                                              '112=tr1',
                                              '10=186'))

        self.assertEquals(0, self.transport.message_received_count)
        self.assertNotEquals(last_time, self.protocol._last_received_time)

    def test_timeout(self):
        """ TestRequest timeout testing """
        self.protocol.heartbeat = 5     # time in secs
        now = datetime.datetime.now()

        # set this to simulate that a TestRequest was sent
        self.protocol._testrequest_id = 'TR1'
        self.protocol._testrequest_time = now - datetime.timedelta(seconds=50)

        # force a timer tick
        with self.assertRaises(FIXTimeoutError):
            self.protocol.on_timer_tick_received()

    def test_simple_send(self):
        """ test simple sending """
        self.assertEquals(0, self.transport.message_sent_count)
        self.transport.send_message(FIXMessage(source=[(8, 'FIX.4.2'),
                                                       (35, 'A'), ]))
        self.assertEquals(1, self.transport.message_sent_count)

    def test_send_seqno(self):
        """ test send sequence numbering """
        seqno = self.protocol._send_seqno
        self.assertEquals(0, self.transport.message_sent_count)
        self.transport.send_message(FIXMessage(source=[(8, 'FIX.4.2'),
                                                       (35, 'A'), ]))
        self.assertEquals(1, self.transport.message_sent_count)
        self.assertEquals(seqno+1, self.protocol._send_seqno)

    def test_send_with_missing_fields(self):
        """ send with missing fields """
        self.assertEquals(0, self.transport.message_sent_count)

        message = FIXMessage(source=[(8, 'FIX.4.2'),
                                     (35, 'A'), ])
        self.assertTrue(34 not in message)
        self.assertTrue(52 not in message)
        self.transport.send_message(message)
        self.assertEquals(1, self.transport.message_sent_count)

        # check for seqno(34) and sendtime(52)
        self.assertTrue(34 in self.transport.last_message_sent)
        self.assertTrue(52 in self.transport.last_message_sent)
