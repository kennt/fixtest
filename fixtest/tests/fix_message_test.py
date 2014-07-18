""" fix.message unit tests

    Copyright (c) 2014 Kenn Takara
    See LICENSE for details

"""

import unittest

from ..fix.constants import FIX
from ..fix.message import checksum, FIXMessage


def to_fix(*args):
    """ Join a series of strings into a FIX binary message,
        a field list separated by \x01
    """
    return '\x01'.join(args) + '\x01'


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

    def test_required_fields(self):
        mess = FIXMessage()
        self.assertEquals(5, len(mess))

        self.assertTrue(8 in mess)
        self.assertTrue(9 in mess)
        self.assertTrue(35 in mess)
        self.assertTrue(49 in mess)
        self.assertTrue(56 in mess)

        items = [(k, v) for k, v in mess.items()]
        # 8,9 are required to be first and second fields, respectively
        self.assertEquals('8', items[0][0])
        self.assertEquals('9', items[1][0])

        # Custom required fields
        mess = FIXMessage(required=[1024, 8, 9])
        self.assertTrue(8 in mess)
        self.assertTrue(9 in mess)
        self.assertTrue(35 not in mess)
        self.assertTrue(1024 in mess)

        items = [(k, v) for k, v in mess.items()]
        self.assertEquals('1024', items[0][0])
        self.assertEquals('8', items[1][0])
        self.assertEquals('9', items[2][0])

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
        self.assertEquals(65, mess[9])
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
        self.assertTrue(False)

    def test_to_binary_group(self):
        self.assertTrue(False)

    def test_to_binary_binarydata(self):
        self.assertTrue(False)

    def test_verify(self):
        self.assertTrue(False)


if __name__ == '__main__':
    unittest.main()
