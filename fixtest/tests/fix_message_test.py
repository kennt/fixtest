""" fix.message unit tests

    Copyright (c) 2014 Kenn Takara
    See LICENSE for details

"""

import collections
import unittest

from fixtest.fix.constants import FIX
from fixtest.fix.message import checksum, FIXMessage
from fixtest.tests.utils import to_fix, to_ordered_dict


class TestFIXMessage(unittest.TestCase):
    # pylint: disable=missing-docstring

    def test_to_fix(self):
        data = to_fix('a', 'b', 'c')
        self.assertEquals('a\x01b\x01c\x01', data)

    def test_checksum(self):
        self.assertEquals(1, checksum('\x01'))
        self.assertEquals(2, checksum('\x01\x01'))
        self.assertEquals(2, checksum('\xFF\x03'))

        # example taken from wikipedia
        self.assertEquals(62,
                          checksum(to_fix('8=FIX.4.2',
                                          '9=65',
                                          '35=A',
                                          '49=SERVER',
                                          '56=CLIENT',
                                          '34=177',
                                          '52=20090107-18:15:16',
                                          '98=0',
                                          '108=30')))

    def test_header_fields(self):
        mess = FIXMessage()
        self.assertEquals(5, len(mess))

        self.assertTrue(8 in mess)
        self.assertTrue(9 in mess)
        self.assertTrue(35 in mess)
        self.assertTrue(49 in mess)
        self.assertTrue(56 in mess)

        items = [(k, v) for k, v in mess.items()]
        # 8,9 are required to be first and second fields, respectively
        self.assertEquals(8, items[0][0])
        self.assertEquals(9, items[1][0])

        # Custom required fields
        mess = FIXMessage(header_fields=[1024, 8, 9])
        self.assertTrue(8 in mess)
        self.assertTrue(9 in mess)
        self.assertTrue(35 not in mess)
        self.assertTrue(1024 in mess)

        items = [(k, v) for k, v in mess.items()]
        self.assertEquals(1024, items[0][0])
        self.assertEquals(8, items[1][0])
        self.assertEquals(9, items[2][0])

    def test_msg_type(self):
        mess = FIXMessage()
        self.assertEquals('', mess[35])
        self.assertEquals('', mess.msg_type())

        mess[35] = FIX.LOGON
        self.assertEquals(FIX.LOGON, mess[35])
        self.assertEquals(FIX.LOGON, mess.msg_type())

    def test_to_binary(self):
        mess = FIXMessage()
        mess[8] = 'FIX.4.2'
        mess[9] = '---'
        mess[35] = 'A'
        mess[49] = 'SERVER'
        mess[56] = 'CLIENT'
        mess[34] = 177
        mess[52] = '20090107-18:15:16'
        mess[98] = 0
        mess[108] = 30
        mess[10] = '---'

        data = mess.to_binary()

        # BodyLength(9) and Checksum(10) should be updated after
        # the to_binary() was called.
        self.assertEquals('65', mess[9])
        self.assertEquals('062', mess[10])

        self.assertEquals(to_fix('8=FIX.4.2',
                                 '9=65',
                                 '35=A',
                                 '49=SERVER',
                                 '56=CLIENT',
                                 '34=177',
                                 '52=20090107-18:15:16',
                                 '98=0',
                                 '108=30',
                                 '10=062'),
                          data)

    def test_to_binary_include(self):
        mess = FIXMessage()
        mess[8] = 'FIX.4.2'
        mess[9] = '---'
        mess[35] = 'A'
        mess[49] = 'SERVER'
        mess[56] = 'CLIENT'
        mess[177] = 'hello'

        data = mess.to_binary(include=[8, 9, 35, 177])
        self.assertEquals(to_fix('8=FIX.4.2',
                                 '9=15',
                                 '35=A',
                                 '177=hello',
                                 '10=212'),
                          data)

    def test_to_binary_exclude(self):
        mess = FIXMessage()
        mess[8] = 'FIX.4.2'
        mess[9] = '---'
        mess[35] = 'A'
        mess[49] = 'SERVER'
        mess[56] = 'CLIENT'
        mess[99] = 'X'
        mess[177] = 'hello'

        data = mess.to_binary(exclude=[35, 177])
        self.assertEquals(to_fix('8=FIX.4.2',
                                 '9=25',
                                 '49=SERVER',
                                 '56=CLIENT',
                                 '99=X',
                                 '10=239'),
                          data)

    def test_to_binary_group(self):
        """ Call to_binary() on a grouped message """
        mess = FIXMessage(header_fields=[8, 9])
        tags = collections.OrderedDict()
        mess[8] = 'FIX.4.2'
        mess[9] = '---'
        tags[110] = 2
        tags[111] = 'abcd'

        mess[100] = [tags, ]
        data = mess.to_binary()

        self.assertEquals(to_fix('8=FIX.4.2',
                                 '9=21',
                                 '100=1',
                                 '110=2',
                                 '111=abcd',
                                 '10=086'),
                          data)

    def test_group_from_list(self):
        """ Call to_binary() on a grouped message from a list """
        mess = FIXMessage(header_fields=[8, 9],
                          source=[(8, 'FIX.4.2'),
                                  (9, '25'),
                                  (49, 'SERVER'),
                                  (56, 'CLIENT'),
                                  (99, 'X')])
        self.assertEquals(to_fix('8=FIX.4.2',
                                 '9=25',
                                 '49=SERVER',
                                 '56=CLIENT',
                                 '99=X',
                                 '10=239'),
                          mess.to_binary())

    def test_nested_group_from_list(self):
        """ Call to_binary() on a nested grouped message from a list """
        # As its difficult to test this, convert the (unordered)
        # dict into an OrderedDict() before inserting (sorting by tag).
        # This makes it easier to do the comparison.
        mess = FIXMessage(
            header_fields=[8, 9],
            source=to_ordered_dict([(8, 'FIX.4.2'),
                                    (100, [{101: 'abc', 102: 'def'},
                                           {101: 'ghi', 103: 'jkl'},
                                           {101: 'mno', 200: [
                                               {201: 'aaa', 202: 'bbb'}]}]),
                                    (99, 'X')]))
        self.assertEquals(to_fix('8=FIX.4.2',
                                 '9=73',
                                 '100=3',
                                 '101=abc',
                                 '102=def',
                                 '101=ghi',
                                 '103=jkl',
                                 '101=mno',
                                 '200=1',
                                 '201=aaa',
                                 '202=bbb',
                                 '99=X',
                                 '10=034'),
                          mess.to_binary())

    def test_to_binary_binarydata(self):
        mess = FIXMessage(header_fields=[8, 9])
        mess[8] = 'FIX.4.2'
        mess[9] = '---'
        mess[110] = 2
        mess[111] = '\x01\x02a\xbbbcd'

        data = mess.to_binary()

        self.assertEquals(to_fix('8=FIX.4.2',
                                 '9=18',
                                 '110=2',
                                 '111=\x01\x02a\xbbbcd',
                                 '10=026'),
                          data)

    def test_verify(self):
        mess = FIXMessage()
        mess[8] = 'FIX.4.2'
        mess[9] = '---'
        mess[35] = 'A'
        mess[49] = 'SERVER'
        mess[56] = 'CLIENT'
        mess[99] = 'X'
        mess[177] = 'hello'

        self.assertTrue(mess.verify(fields=[(8, 'FIX.4.2'), (35, 'A')]))
        self.assertFalse(mess.verify(fields=[(8, 'NOFIX')]))

        self.assertTrue(mess.verify(exists=[8, 35, 177]))
        self.assertFalse(mess.verify(exists=[9, 8, 2000]))

        self.assertTrue(mess.verify(not_exists=[2000, 20001]))
        self.assertFalse(mess.verify(not_exists=[177]))

        self.assertTrue(mess.verify(fields=[(99, 'X')],
                                    exists=[56, 99, 177],
                                    not_exists=[2001, 2002, 2003]))

if __name__ == '__main__':
    unittest.main()
