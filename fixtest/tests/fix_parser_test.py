""" fix.parser unit tests

    Copyright (c) 2014 Kenn Takara
    See LICENSE for details

"""

import unittest

from ..fix.parser import FIXParser
from ..fix.parser import FIXMessageParseError, FIXMessageLengthExceededError
from ..tests.utils import to_fix

# pylint: disable=too-many-public-methods
# pylint: disable=missing-docstring


class TestFIXParser(unittest.TestCase):

    class MockFIXReceiver(object):
        def __init__(self):
            self.count = 0
            self.last_received_message = None
            self.last_error = None

        def on_message_received(self, message):
            self.count += 1
            self.last_received_message = message

        def on_error(self, error):
            self.last_error = error

    def __init__(self, *args, **kwargs):
        super(TestFIXParser, self).__init__(*args, **kwargs)

        self.receiver = None

    def setUp(self):
        self.receiver = TestFIXParser.MockFIXReceiver()

    def test_simple_message(self):
        """ Basic data test. """
        parser = FIXParser(self.receiver.on_message_received,
                           self.receiver.on_error,
                           header_fields=[8, 9])
        parser.on_data_received(to_fix('8=FIX.4.2',
                                       '9=32'
                                       '35=A',
                                       '10=100'))
        self.assertEquals(1, self.receiver.count)

        message = self.last_received_message
        self.assertIsNotNone(message)
        self.assertEquals(4, len(message))
        self.assertTrue(message.verify(fields=[(8, 'FIX.4.2'),
                                               (9, '32'),
                                               (35, 'A'),
                                               (10, 100)]))

    def test_partial_message(self):
        """ Test for partial input. """
        parser = FIXParser(self.receiver.on_message_received,
                           self.receiver.on_error,
                           header_fields=[8, 9])
        self.assertEquals(0, self.receiver.count)
        parser.on_data_received(to_fix('8=FIX.4.2',
                                       '9=32'
                                       '35=A'))
        self.assertEquals(0, self.receiver.count)

    def test_bad_syntax(self):
        """ Test for various bad syntax cases """
        parser = FIXParser(self.receiver.on_message_received,
                           self.receiver.on_error,
                           header_fields=[8, 9])

        # Tag ID is not a number
        parser.on_data_received(to_fix('8=FIX.4.2',
                                       '9=32'
                                       'abcd=A'))
        self.assertIsNotNone(self.receiver.last_error)
        self.assertTrue(isinstance(self.receiver.last_error,
                                   FIXMessageParseError))
        self.receiver.last_error = None

        # Missing '=' and value portion
        parser.on_data_received(to_fix('8=FIX.4',
                                       '9=32'
                                       '35'))
        self.assertIsNotNone(self.receiver.last_error)
        self.assertTrue(isinstance(self.receiver.last_error,
                                   FIXMessageParseError))
        self.receiver.last_error = None

        # Mising tag ID portion
        parser.on_data_received(to_fix('8=FIX.4',
                                       '9=32'
                                       '=A'))
        self.assertIsNotNone(self.receiver.last_error)
        self.assertTrue(isinstance(self.receiver.last_error,
                                   FIXMessageParseError))
        self.receiver.last_error = None

    def test_message_too_large(self):
        """ Test for long message """
        parser = FIXParser(self.receiver.on_message_received,
                           self.receiver.on_error,
                           header_fields=[8, 9],
                           max_length=100)

        # Tag ID is not a number
        parser.on_data_received(to_fix('8=FIX.4.2',
                                       '9=32'
                                       '42=A' + 'BB'*100))
        self.assertIsNotNone(self.receiver.last_error)
        self.assertTrue(isinstance(self.receiver.last_error,
                                   FIXMessageLengthExceededError))

    # test bad checksum
    # test too long
    # test incorrect binary data length
    # test that error causes reset
    # test bad binary fields
    # test bad group fields

    # test header fields
    # test binary fields
    # test group fields
    # test multiple messages in data stream
    # test one byte at a time
    # test partial reception of binary data
    # test multiple group nestings
