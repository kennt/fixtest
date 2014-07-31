""" fix.protocol unit tests

    Copyright (c) 2014 Kenn Takara
    See LICENSE for details

"""

import unittest

from ..fix.message import FIXMessage
from ..fix.protocol import FIXProtocol, FIXDataError
from ..tests.utils import to_fix

# pylint: disable=too-many-public-methods
# pylint: disable=missing-docstring


class TestFIXProtocol(unittest.TestCase):

    class MockFIXTransport(object):
        def __init__(self):
            self.message_received_count = 0
            self.last_message_received = None

            self.message_sent_count = 0
            self.last_message_sent = None

            self.timeout_received_count = 0

        def on_message_received(self, message):
            self.message_received_count += 1
            self.last_message_received = message

        def send_message(self, message):
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
                                        'required_fields': [],
                                        'header_fields': [],
                                        'binary_fields': [],
                                        'group_fields': {},
                                    })

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
        self.assertTrue(False)

    def test_header_fields_in_order(self):
        """ Test for out-of-order header fields """
        self.assertTrue(False)

    def test_send_heartbeat(self):
        """ Test heartbeat sending """
        self.assertTrue(False)

    def test_send_testrequest(self):
        """ Test TestRequest sending """
        self.assertTrue(False)

    def test_receive_heartbeat(self):
        """ Test receiving heartbeat """
        self.assertTrue(False)

    def test_receive_testrequest(self):
        """ test receiving testrequest """
        self.assertTrue(False)

    def test_timeout(self):
        """ timeout testing """
        self.assertTrue(False)

    def test_send_with_missing_fields(self):
        """ send with missing fields """
        self.assertTrue(False)

    def test_send_with_binary_data(self):
        """ send binary data """
        self.assertTrue(False)

    def test_send_with_groups(self):
        """ send message with groups """
        self.assertTrue(False)

    def test_send_with_nested_groups(self):
        """ send message with nested groups """
        self.assertTrue(False)
