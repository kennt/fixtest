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

        def on_error_received(self, error):
            self.last_error = error

    def __init__(self, *args, **kwargs):
        super(TestFIXParser, self).__init__(*args, **kwargs)

        self.receiver = None

    def setUp(self):
        self.receiver = TestFIXParser.MockFIXReceiver()

    def test_simple_message(self):
        """ Basic function test. """
        parser = FIXParser(self.receiver,
                           header_fields=[8, 9])

        self.assertFalse(parser.is_parsing)
        parser.on_data_received(to_fix('8=FIX.4.2',
                                       '9=32',
                                       '35=A',
                                       '10=100'))
        self.assertFalse(parser.is_parsing)
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
        parser = FIXParser(self.receiver,
                           header_fields=[8, 9])

        self.assertFalse(parser.is_parsing)
        self.assertEquals(0, self.receiver.count)
        parser.on_data_received(to_fix('8=FIX.4.2',
                                       '9=32',
                                       '35=A'))
        self.assertEquals(0, self.receiver.count)
        self.assertTrue(parser.is_parsing)

    def test_bad_syntax(self):
        """ Test for various bad syntax cases """
        parser = FIXParser(self.receiver,
                           header_fields=[8, 9])

        # Tag ID is not a number
        parser.on_data_received(to_fix('8=FIX.4.2',
                                       '9=32',
                                       'abcd=A'))
        self.assertIsNotNone(self.receiver.last_error)
        self.assertTrue(isinstance(self.receiver.last_error,
                                   FIXMessageParseError))
        self.receiver.last_error = None

        # Missing '=' and value portion
        parser.on_data_received(to_fix('8=FIX.4',
                                       '9=32',
                                       '35'))
        self.assertIsNotNone(self.receiver.last_error)
        self.assertTrue(isinstance(self.receiver.last_error,
                                   FIXMessageParseError))
        self.receiver.last_error = None

        # Missing tag ID portion
        parser.on_data_received(to_fix('8=FIX.4',
                                       '9=32',
                                       '=A'))
        self.assertIsNotNone(self.receiver.last_error)
        self.assertTrue(isinstance(self.receiver.last_error,
                                   FIXMessageParseError))

    def test_message_too_large(self):
        """ Test for too long message """
        parser = FIXParser(self.receiver,
                           header_fields=[8, 9],
                           max_length=100)

        parser.on_data_received(to_fix('8=FIX.4.2',
                                       '9=32',
                                       '42=A' + 'BB'*100))
        self.assertIsNotNone(self.receiver.last_error)
        self.assertTrue(isinstance(self.receiver.last_error,
                                   FIXMessageLengthExceededError))

    def test_message_bad_checksum(self):
        """ Test for message with a bad checksum """
        parser = FIXParser(self.receiver,
                           header_fields=[8, 9],
                           max_length=100)

        parser.on_data_received(to_fix('8=FIX.4.2',
                                       '9=32',
                                       '42=A',
                                       '10=000'))
        self.assertIsNotNone(self.receiver.last_error)
        self.assertTrue(isinstance(self.receiver.last_error,
                                   FIXMessageParseError))

    def test_message_bad_binary_length(self):
        """ Test for message with missing binary data """
        parser = FIXParser(self.receiver,
                           header_fields=[8, 9],
                           binary_fields=[1000],
                           max_length=100)

        parser.on_data_received(to_fix('8=FIX.4.2',
                                       '9=32',
                                       '42=A',
                                       '1000=2',
                                       '1001=abababababab',
                                       '10=000'))
        self.assertIsNotNone(self.receiver.last_error)
        self.assertTrue(isinstance(self.receiver.last_error,
                                   FIXMessageParseError))

        self.receiver.last_error = None
        parser.on_data_received(to_fix('8=FIX.4.2',
                                       '9=32',
                                       '42=A',
                                       '1000=20',
                                       '1001=ab',
                                       '10=000'))
        self.assertIsNotNone(self.receiver.last_error)
        self.assertTrue(isinstance(self.receiver.last_error,
                                   FIXMessageParseError))

        # Note that we could have an error where the length of the
        # binary field is longer than the message.  In this case, the
        # operation should time out, but that is not the responsibility of
        # the parser.

    def test_parser_reset(self):
        """ Test that the parser resets on an error """
        parser = FIXParser(self.receiver,
                           header_fields=[8, 9])

        # Tag ID is not a number
        self.assertFalse(parser.is_parsing)
        parser.on_data_received(to_fix('8=FIX.4.2',
                                       '9=32',
                                       'abcd=A'))
        self.assertIsNotNone(self.receiver.last_error)
        self.assertTrue(isinstance(self.receiver.last_error,
                                   FIXMessageParseError))
        self.assertFalse(parser.is_parsing)

    def test_bad_binary_fields(self):
        """ Test bad binary fields """
        parser = FIXParser(self.receiver,
                           binary_fields=[1000],
                           header_fields=[8, 9])

        # Missing binary value portion of binary field
        parser.on_data_received(to_fix('8=FIX.4.2',
                                       '9=32',
                                       '1000=10',
                                       '10=001'))
        self.assertIsNotNone(self.receiver.last_error)
        self.assertTrue(isinstance(self.receiver.last_error,
                                   FIXMessageParseError))

        # Missing binary length portion (the only time this
        # really impacts something is if the field has an
        # embedded \x01).
        parser.on_data_received(to_fix('8=FIX.4.2',
                                       '9=32',
                                       '1001=1010\x011010',
                                       '10=001'))
        self.assertIsNotNone(self.receiver.last_error)
        self.assertTrue(isinstance(self.receiver.last_error,
                                   FIXMessageParseError))

        parser.on_data_received(to_fix('8=FIX.4.2',
                                       '9=32',
                                       '1001=10101010',
                                       '10=001'))
        self.assertIsNone(self.receiver.last_error)
        self.assertEquals(1, self.receiver.count)
        self.assertIsNotNone(self.receiver.last_received_message)

    def test_header_fields(self):
        """ Header field testing. """
        parser = FIXParser(self.receiver,
                           header_fields=[8, 9, 320])

        parser.on_data_received(to_fix('8=FIX.4.2',
                                       '9=32',
                                       '35=A',
                                       '10=100'))
        self.assertEquals(1, self.receiver.count)

        message = self.last_received_message
        self.assertIsNotNone(message)
        message[320] = 'hello there'
        self.assertEquals(5, len(message))

        # verify the order of the message
        items = [(k, v) for k, v in message.items()]
        self.assertEquals('8', items[0][0])
        self.assertEquals('9', items[1][0])
        self.assertEquals('320', items[2][0])

    def test_binary_fields(self):
        """ Binary field testing. """
        parser = FIXParser(self.receiver,
                           binary_fields=[1001, 1010],
                           header_fields=[8, 9])

        # Test with embedded binary \x01
        parser.on_data_received(to_fix('8=FIX.4.2',
                                       '9=32',
                                       '1000=5',
                                       '1001=\x01\x02\x03\x04\x05',
                                       '10=100'))
        self.assertEquals(1, self.receiver.count)

        message = self.last_received_message
        self.assertIsNotNone(message)
        self.assertEquals(5, len(message))
        self.assertTrue(message.verify(fields=[(8, 'FIX.4.2'),
                                               (9, '32'),
                                               (1000, '5'),
                                               (1001, '\x01\x02\x03\x04\x05'),
                                               (10, 100)]))

        # Test with embedded '=' signs
        parser.on_data_received(to_fix('8=FIX.4.2',
                                       '9=32',
                                       '1000=5',
                                       '1001=31=20',
                                       '10=100'))
        self.assertEquals(2, self.receiver.count)

        message = self.last_received_message
        self.assertIsNotNone(message)
        self.assertEquals(5, len(message))
        self.assertTrue(message.verify(fields=[(8, 'FIX.4.2'),
                                               (9, '32'),
                                               (1000, '5'),
                                               (1001, '31=20'),
                                               (10, 100)]))

    def test_simple_group_fields(self):
        """ Simple group field testing. """
        parser = FIXParser(self.receiver,
                           group_fields=[(100, [101, 102, 200]),
                                         (200, [201, 202])],
                           header_fields=[8, 9])

        parser.on_data_received(to_fix('8=FIX.4.2',
                                       '9=32',
                                       '100=1',
                                       '101=a',
                                       '102=b',
                                       '10=100'))
        self.assertEquals(1, self.receiver.count)

        message = self.last_received_message
        self.assertIsNotNone(message)
        self.assertEquals(4, len(message))

        self.assertIsTrue(100 in message)
        self.assertEquals(1, len(message[100]))

        group = message[100]
        self.assertIsNotNone(group)
        self.assertEquals(1, len(group))
        self.assertEquals(2, len(group[0]))
        self.assertTrue(101 in group[0])
        self.assertTrue(102 in group[0])
        self.assertEquals('a', group[0][101])
        self.assertEquals('b', group[0][102])

    def test_multiple_groups(self):
        """ Test the receiving of multiple groups """
        parser = FIXParser(self.receiver,
                           group_fields=[(100, [101, 102, 200]),
                                         (200, [201, 202])],
                           header_fields=[8, 9])

        parser.on_data_received(to_fix('8=FIX.4.2',
                                       '9=32',
                                       '100=2',
                                       '101=a',
                                       '102=b',
                                       '101=aa',
                                       '102=bb',
                                       '10=100'))
        self.assertEquals(1, self.receiver.count)

        message = self.last_received_message
        self.assertIsNotNone(message)
        self.assertEquals(4, len(message))

        self.assertIsTrue(100 in message)
        self.assertEquals(2, len(message[100]))

        group = message[100]
        self.assertIsNotNone(group)
        self.assertEquals(2, len(group))
        self.assertEquals(2, len(group[0]))
        self.assertTrue(101 in group[0])
        self.assertTrue(102 in group[0])
        self.assertEquals('a', group[0][101])
        self.assertEquals('b', group[0][102])
        self.assertEquals(2, len(group[1]))
        self.assertTrue(101 in group[1])
        self.assertTrue(102 in group[1])
        self.assertEquals('aa', group[1][101])
        self.assertEquals('bb', group[1][102])

    def test_nested_groups(self):
        """ Test the receiving of nested groups """
        parser = FIXParser(self.receiver,
                           group_fields=[(100, [101, 102, 200]),
                                         (200, [201, 202])],
                           header_fields=[8, 9])

        parser.on_data_received(to_fix('8=FIX.4.2',
                                       '9=32',
                                       '100=1',
                                       '101=a',
                                       '102=b',
                                       '200=1',
                                       '201=abc',
                                       '202=def',
                                       '10=100'))
        self.assertEquals(1, self.receiver.count)

        message = self.last_received_message
        self.assertIsNotNone(message)
        self.assertEquals(4, len(message))

        self.assertIsTrue(100 in message)
        self.assertEquals(1, len(message[100]))

        group = message[100]
        self.assertIsNotNone(group)
        self.assertEquals(1, len(group))
        self.assertEquals(3, len(group[0]))
        self.assertTrue(101 in group[0])
        self.assertTrue(102 in group[0])
        self.assertTrue(200 in group[0])
        self.assertEquals('a', group[0][101])
        self.assertEquals('b', group[0][102])

        subgroup = group[0]
        self.assertIsNotNone(subgroup)
        self.assertEquals(1, len(subgroup))
        self.assertEquals(2, len(subgroup[0]))
        self.assertTrue(201 in subgroup[0])
        self.assertTrue(202 in subgroup[0])
        self.assertEquals('abc', subgroup[0][201])
        self.assertEquals('def', subgroup[0][202])

    def test_multiple_message(self):
        """ Receive two messages in one data buffer """
        parser = FIXParser(self.receiver,
                           header_fields=[8, 9])

        self.assertFalse(parser.is_parsing)
        parser.on_data_received(to_fix('8=FIX.4.2',
                                       '9=32',
                                       '35=A',
                                       '10=100',
                                       '8=FIX.4.2.',
                                       '9=36',
                                       '35=E',
                                       '99=forsooth',
                                       '10=100'))
        self.assertFalse(parser.is_parsing)
        self.assertEquals(2, self.receiver.count)

        message = self.last_received_message
        self.assertIsNotNone(message)
        self.assertEquals(5, len(message))
        self.assertTrue(message.verify(fields=[(8, 'FIX.4.2'),
                                               (9, '36'),
                                               (35, 'E'),
                                               (99, 'forsooth'),
                                               (10, 100)]))

    def test_one_byte_at_a_time(self):
        """ Receive a message split up into single bytes """
        parser = FIXParser(self.receiver,
                           header_fields=[8, 9])

        text = to_fix('8=FIX.4.2',
                      '9=32',
                      '35=A',
                      '919=this',
                      '955=that',
                      '10=100')
        for c in text:
            parser.on_data_received(c)

        self.assertFalse(parser.is_parsing)
        self.assertEquals(1, self.receiver.count)

        message = self.last_received_message
        self.assertIsNotNone(message)
        self.assertEquals(6, len(message))
        self.assertTrue(message.verify(fields=[(8, 'FIX.4.2'),
                                               (9, '32'),
                                               (35, 'A'),
                                               (919, 'this'),
                                               (955, 'that'),
                                               (10, 100)]))

    def test_partial_binary_data(self):
        """ Receive a piece of binary data split into two parts """
        parser = FIXParser(self.receiver,
                           binary_fields=[99],
                           header_fields=[8, 9])

        text = to_fix('8=FIX.4.2',
                      '9=32',
                      '35=A') + '99=5\x01100=12'
        text2 = to_fix('345',
                       '919=this',
                       '955=that',
                       '10=100')
        parser.on_data_received(text)
        self.assertTrue(parser.is_parsing)

        parser.on_data_received(text2)
        self.assertFalse(parser.is_parsing)

        self.assertEquals(1, self.receiver.count)

        message = self.last_received_message
        self.assertIsNotNone(message)
        self.assertEquals(6, len(message))
        self.assertTrue(message.verify(fields=[(8, 'FIX.4.2'),
                                               (9, '32'),
                                               (35, 'A'),
                                               (99, '5'),
                                               (100, '12345'),
                                               (10, 100)]))
