""" fix.parser unit tests

    Copyright (c) 2014 Kenn Takara
    See LICENSE for details

"""

import unittest

from fixtest.fix.parser import FIXParser
from fixtest.fix.parser import FIXParserError, FIXLengthTooLongError
from fixtest.tests.utils import to_fix

# pylint: disable=too-many-public-methods
# pylint: disable=missing-docstring


class MockFIXReceiver(object):
    def __init__(self):
        self.count = 0
        self.last_received_message = None
        self.last_error = None

    def on_message_received(self, message, message_length, checksum):
        # pylint: disable=unused-argument
        self.count += 1
        self.last_received_message = message

    def on_error_received(self, error):
        # pylint: disable=no-self-use
        raise error


class TestFIXParserInternals(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(TestFIXParserInternals, self).__init__(*args, **kwargs)

        self.receiver = None

    def setUp(self):
        self.receiver = MockFIXReceiver()

    def test_parse_field(self):
        """ Basic _parse_field function test """
        parser = FIXParser(self.receiver)

        field = parser._parse_field('8=a')
        self.assertEquals(8, field[0])
        self.assertEquals('a', field[1])

    def test_parse_field_bad_input(self):
        """ Test bad _parse_field inputs """
        parser = FIXParser(self.receiver)

        # missing '='
        with self.assertRaises(FIXParserError):
            parser._parse_field('abcde')

        # bad tag id
        with self.assertRaises(FIXParserError):
            parser._parse_field('a=a')

        # missing tag id
        with self.assertRaises(FIXParserError):
            parser._parse_field('=a')

        # bad tag id
        with self.assertRaises(FIXParserError):
            parser._parse_field('10b=a')


class TestFIXParser(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(TestFIXParser, self).__init__(*args, **kwargs)

        self.receiver = None

    def setUp(self):
        self.receiver = MockFIXReceiver()

    def test_simple_message(self):
        """ Basic function test. """
        parser = FIXParser(self.receiver,
                           header_fields=[8, 9])

        self.assertFalse(parser.is_parsing)

        # message taken from wikipedia article
        parser.on_data_received(to_fix('8=FIX.4.2',
                                       '9=65',
                                       '35=A',
                                       '49=SERVER',
                                       '56=CLIENT',
                                       '34=177',
                                       '52=20090107-18:15:16',
                                       '98=0',
                                       '108=30',
                                       '10=062'))

        self.assertFalse(parser.is_parsing)
        self.assertEquals(1, self.receiver.count)

        message = self.receiver.last_received_message
        self.assertIsNotNone(message)
        self.assertEquals(10, len(message))
        self.assertTrue(message.verify(fields=[(8, 'FIX.4.2'),
                                               (9, '65'),
                                               (35, 'A'),
                                               (10, '062')]))

    def test_message_starts_incorrectly(self):
        """ Message must start with tag 8 """
        parser = FIXParser(self.receiver,
                           header_fields=[8, 9])

        # message does not start with tag 8
        with self.assertRaises(FIXParserError):
            parser.on_data_received(to_fix('18=FIX.4.2',
                                           '9=32',
                                           '8=FIX.4.2',
                                           '35=A',
                                           '10=100'))

        # unexpected tag 8
        with self.assertRaises(FIXParserError):
            parser.on_data_received(to_fix('8=FIX.4.2',
                                           '9=32',
                                           '8=abcdef',
                                           '35=A',
                                           '10=100'))

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
        with self.assertRaises(FIXParserError):
            parser.on_data_received(to_fix('8=FIX.4.2',
                                           '9=32',
                                           'abcd=A'))

        # Missing '=' and value portion
        with self.assertRaises(FIXParserError):
            parser.on_data_received(to_fix('8=FIX.4',
                                           '9=32',
                                           '35'))

        # Missing tag ID portion
        with self.assertRaises(FIXParserError):
            parser.on_data_received(to_fix('8=FIX.4',
                                           '9=32',
                                           '=A'))

    def test_message_too_large(self):
        """ Test for too long message """
        parser = FIXParser(self.receiver,
                           header_fields=[8, 9],
                           max_length=100)

        with self.assertRaises(FIXLengthTooLongError):
            parser.on_data_received(to_fix('8=FIX.4.2',
                                           '9=32',
                                           '42=A' + 'BB'*100))

    def test_message_bad_binary_length(self):
        """ Test for message with missing binary data """
        parser = FIXParser(self.receiver,
                           header_fields=[8, 9],
                           binary_fields=[1000],
                           max_length=100)

        # length too short
        with self.assertRaises(FIXParserError):
            parser.on_data_received(to_fix('8=FIX.4.2',
                                           '9=32',
                                           '42=A',
                                           '1000=2',
                                           '1001=abababababab',
                                           '10=000'))

        # length too long
        # This will not raise an error
        parser.on_data_received(to_fix('8=FIX.4.2',
                                       '9=32',
                                       '42=A',
                                       '1000=20',
                                       '1001=ab',
                                       '10=000'))
        self.assertEquals(0, self.receiver.count)
        self.assertTrue(parser.is_parsing)

        # Note that we could have an error where the length of the
        # binary field is longer than the message.  In this case, the
        # operation should time out, but that is not the responsibility of
        # the parser.

    def test_message_binary_too_long(self):
        """ Test for message with missing binary data """
        parser = FIXParser(self.receiver,
                           header_fields=[8, 9],
                           binary_fields=[1000],
                           max_length=100)

        # length too short
        with self.assertRaises(FIXLengthTooLongError):
            parser.on_data_received(to_fix('8=FIX.4.2',
                                           '9=32',
                                           '42=A',
                                           '1000=128',
                                           '1001=abababababab',
                                           '10=000'))

    def test_parser_reset(self):
        """ Test that the parser resets on an error """
        parser = FIXParser(self.receiver,
                           header_fields=[8, 9])

        # Tag ID is not a number
        self.assertFalse(parser.is_parsing)
        with self.assertRaises(FIXParserError):
            parser.on_data_received(to_fix('8=FIX.4.2',
                                           '9=32',
                                           'abcd=A'))
        self.assertFalse(parser.is_parsing)

    def test_bad_binary_fields(self):
        """ Test bad binary fields """
        parser = FIXParser(self.receiver,
                           binary_fields=[1000],
                           header_fields=[8, 9])

        # Missing binary value portion of binary field
        # BUGBUG: This can cause some problems, because the parser
        # does not attempt to validate until the entire
        # field has been read in.  Which this will fail because
        # the length goes past the end of the message.
        # For now, live with this.
        with self.assertRaises(FIXParserError):
            parser.on_data_received(to_fix('8=FIX.4.2',
                                           '9=32',
                                           '1000=5',
                                           '999=11',
                                           '10=001'))

        # Missing binary length portion (the only time this
        # really impacts something is if the field has an
        # embedded \x01).
        with self.assertRaises(FIXParserError):
            parser.on_data_received(to_fix('8=FIX.4.2',
                                           '9=32',
                                           '1001=1010\x011010',
                                           '10=001'))

        parser.on_data_received(to_fix('8=FIX.4.2',
                                       '9=14',
                                       '1001=10101010',
                                       '10=127'))
        self.assertIsNone(self.receiver.last_error)
        self.assertEquals(1, self.receiver.count)
        self.assertIsNotNone(self.receiver.last_received_message)

    def test_header_fields(self):
        """ Header field testing. """
        parser = FIXParser(self.receiver,
                           header_fields=[8, 9, 320])

        parser.on_data_received(to_fix('8=FIX.4.2',
                                       '9=5',
                                       '35=A',
                                       '10=178'))
        self.assertEquals(1, self.receiver.count)

        message = self.receiver.last_received_message
        self.assertIsNotNone(message)
        message[320] = 'hello there'
        self.assertEquals(5, len(message))

        # verify the order of the message
        items = [(k, v) for k, v in message.items()]
        self.assertEquals(8, items[0][0])
        self.assertEquals(9, items[1][0])
        self.assertEquals(320, items[2][0])

    def test_binary_fields(self):
        """ Binary field testing. """
        parser = FIXParser(self.receiver,
                           binary_fields=[1000, 1010],
                           header_fields=[8, 9])

        # Test with embedded binary \x01
        parser.on_data_received(to_fix('8=FIX.4.2',
                                       '9=18',
                                       '1000=5',
                                       '1001=\x01\x02\x03\x04\x05',
                                       '10=066'))
        self.assertEquals(1, self.receiver.count)

        message = self.receiver.last_received_message
        self.assertIsNotNone(message)
        self.assertEquals(5, len(message))
        self.assertTrue(message.verify(fields=[(8, 'FIX.4.2'),
                                               (9, '18'),
                                               (1000, '5'),
                                               (1001, '\x01\x02\x03\x04\x05'),
                                               (10, '066')]))

        # Test with embedded '=' signs
        parser.on_data_received(to_fix('8=FIX.4.2',
                                       '9=18',
                                       '1000=5',
                                       '1001=31=20',
                                       '10=054'))
        self.assertEquals(2, self.receiver.count)

        message = self.receiver.last_received_message
        self.assertIsNotNone(message)
        self.assertEquals(5, len(message))
        self.assertTrue(message.verify(fields=[(8, 'FIX.4.2'),
                                               (9, '18'),
                                               (1000, '5'),
                                               (1001, '31=20'),
                                               (10, '054')]))

    def test_simple_group_fields(self):
        """ Simple group field testing. """
        parser = FIXParser(self.receiver,
                           group_fields={100: [101, 102, 200],
                                         200: [201, 202], },
                           header_fields=[8, 9])

        parser.on_data_received(to_fix('8=FIX.4.2',
                                       '9=18',
                                       '100=1',
                                       '101=a',
                                       '102=b',
                                       '10=099'))
        self.assertEquals(1, self.receiver.count)

        message = self.receiver.last_received_message
        self.assertIsNotNone(message)
        self.assertEquals(4, len(message))

        self.assertTrue(100 in message)
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
                           group_fields={100: [101, 102, 200],
                                         200: [201, 202], },
                           header_fields=[8, 9])

        parser.on_data_received(to_fix('8=FIX.4.2',
                                       '9=32',
                                       '100=2',
                                       '101=a',
                                       '102=b',
                                       '101=aa',
                                       '102=bb',
                                       '10=135'))
        self.assertEquals(1, self.receiver.count)

        message = self.receiver.last_received_message
        self.assertIsNotNone(message)
        self.assertEquals(4, len(message))

        self.assertTrue(100 in message)
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
                           debug=True,
                           group_fields={100: [101, 102, 200],
                                         200: [201, 202], },
                           header_fields=[8, 9])

        parser.on_data_received(to_fix('8=FIX.4.2',
                                       '9=40',
                                       '100=1',
                                       '101=a',
                                       '102=b',
                                       '200=1',
                                       '201=abc',
                                       '202=def',
                                       '10=087'))
        self.assertEquals(1, self.receiver.count)

        message = self.receiver.last_received_message
        self.assertIsNotNone(message)
        self.assertEquals(4, len(message))

        self.assertTrue(100 in message)
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
        self.assertEquals(3, len(subgroup))
        self.assertEquals(1, len(subgroup[200]))
        subgroup200 = subgroup[200]
        self.assertEquals(2, len(subgroup200[0]))
        self.assertTrue(201 in subgroup200[0])
        self.assertTrue(202 in subgroup200[0])
        self.assertEquals('abc', subgroup200[0][201])
        self.assertEquals('def', subgroup200[0][202])

    def test_multiple_message(self):
        """ Receive two messages in one data buffer """
        parser = FIXParser(self.receiver,
                           header_fields=[8, 9])

        self.assertFalse(parser.is_parsing)
        parser.on_data_received(to_fix('8=FIX.4.2',
                                       '9=5',
                                       '35=A',
                                       '10=178',
                                       '8=FIX.4.2',
                                       '9=17',
                                       '35=E',
                                       '99=forsooth',
                                       '10=013'))
        self.assertFalse(parser.is_parsing)
        self.assertEquals(2, self.receiver.count)

        message = self.receiver.last_received_message
        self.assertIsNotNone(message)
        self.assertEquals(5, len(message))
        self.assertTrue(message.verify(fields=[(8, 'FIX.4.2'),
                                               (9, '17'),
                                               (35, 'E'),
                                               (99, 'forsooth'),
                                               (10, '013')]))

    def test_one_byte_at_a_time(self):
        """ Receive a message split up into single bytes """
        parser = FIXParser(self.receiver,
                           header_fields=[8, 9])

        text = to_fix('8=FIX.4.2',
                      '9=23',
                      '35=A',
                      '919=this',
                      '955=that',
                      '10=013')
        for c in text:
            parser.on_data_received(c)

        self.assertFalse(parser.is_parsing)
        self.assertEquals(1, self.receiver.count)

        message = self.receiver.last_received_message
        self.assertIsNotNone(message)
        self.assertEquals(6, len(message))
        self.assertTrue(message.verify(fields=[(8, 'FIX.4.2'),
                                               (9, '23'),
                                               (35, 'A'),
                                               (919, 'this'),
                                               (955, 'that'),
                                               (10, '013')]))

    def test_partial_binary_data(self):
        """ Receive a piece of binary data split into two parts """
        parser = FIXParser(self.receiver,
                           binary_fields=[99],
                           header_fields=[8, 9])

        text = to_fix('8=FIX.4.2',
                      '9=38',
                      '35=A') + '99=5\x01100=12'
        text2 = to_fix('345',
                       '919=this',
                       '955=that',
                       '10=198')
        parser.on_data_received(text)
        self.assertTrue(parser.is_parsing)

        parser.on_data_received(text2)
        self.assertFalse(parser.is_parsing)

        self.assertEquals(1, self.receiver.count)

        message = self.receiver.last_received_message
        self.assertIsNotNone(message)
        self.assertEquals(8, len(message))
        self.assertTrue(message.verify(fields=[(8, 'FIX.4.2'),
                                               (9, '38'),
                                               (35, 'A'),
                                               (99, '5'),
                                               (100, '12345'),
                                               (919, 'this'),
                                               (955, 'that'),
                                               (10, '198')]))

    def test_grouped_binary_fields(self):
        """ Test binary fields that are in a group. """
        parser = FIXParser(self.receiver,
                           debug=True,
                           group_fields={200: [201, 202, 99, 100]},
                           binary_fields=[99],
                           header_fields=[8, 9])

        text = to_fix('8=FIX.4.2',
                      '9=80',
                      '35=A',
                      '200=2',
                      '201=aabc',
                      '99=5',
                      '100=abcde',
                      '201=zzzaa',
                      '202=myname',
                      '99=5',
                      '100=zztop',
                      '955=that',
                      '10=201')
        parser.on_data_received(text)
        self.assertFalse(parser.is_parsing)

        self.assertEquals(1, self.receiver.count)

        message = self.receiver.last_received_message
        self.assertIsNotNone(message)
        self.assertEquals(6, len(message))
        self.assertEquals(2, len(message[200]))
        self.assertTrue(200 in message)
        self.assertTrue(955 in message)
        subgroup = message[200][0]
        self.assertEquals(3, len(subgroup))
        self.assertTrue(201 in subgroup)
        self.assertTrue(99 in subgroup)
        self.assertTrue(100 in subgroup)
        subgroup = message[200][1]
        self.assertEquals(4, len(subgroup))
        self.assertTrue(201 in subgroup)
        self.assertTrue(202 in subgroup)
        self.assertTrue(99 in subgroup)
        self.assertTrue(100 in subgroup)

    def test_multiple_nested_groups(self):
        """ Test the receiving of multiple nested groups """
        parser = FIXParser(self.receiver,
                           debug=True,
                           group_fields={100: [101, 102, 200],
                                         200: [201, 202], },
                           header_fields=[8, 9])

        parser.on_data_received(to_fix('8=FIX.4.2',
                                       '9=60',
                                       '100=2',
                                       '101=a',
                                       '102=b',
                                       '200=2',
                                       '201=abc',
                                       '202=def',
                                       '201=zzz',
                                       '101=c',
                                       '102=d',
                                       '10=002'))
        self.assertEquals(1, self.receiver.count)

        message = self.receiver.last_received_message
        print message.store
        self.assertIsNotNone(message)
        self.assertEquals(4, len(message))

        self.assertTrue(100 in message)
        self.assertEquals(2, len(message[100]))

        group = message[100]
        self.assertIsNotNone(group)
        self.assertEquals(2, len(group))
        self.assertEquals(3, len(group[0]))
        self.assertTrue(101 in group[0])
        self.assertTrue(102 in group[0])
        self.assertTrue(200 in group[0])
        self.assertEquals('a', group[0][101])
        self.assertEquals('b', group[0][102])
        self.assertEquals(2, len(group[1]))
        self.assertTrue(101 in group[1])
        self.assertTrue(102 in group[1])
        self.assertTrue(200 not in group[1])
        self.assertEquals('c', group[1][101])
        self.assertEquals('d', group[1][102])

        subgroup = group[0]
        self.assertIsNotNone(subgroup)
        self.assertEquals(3, len(subgroup))
        self.assertEquals(2, len(subgroup[200]))
        subgroup200 = subgroup[200]
        self.assertEquals(2, len(subgroup200[0]))
        self.assertTrue(201 in subgroup200[0])
        self.assertTrue(202 in subgroup200[0])
        self.assertEquals('abc', subgroup200[0][201])
        self.assertEquals('def', subgroup200[0][202])
        self.assertEquals(1, len(subgroup200[1]))
        self.assertTrue(201 in subgroup200[1])
        self.assertTrue(202 not in subgroup200[1])
        self.assertEquals('zzz', subgroup200[1][201])
