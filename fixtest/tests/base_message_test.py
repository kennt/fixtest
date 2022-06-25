""" base.message unit tests

    Copyright (c) 2014-2022 Kenn Takara
    See LICENSE for details

"""
import collections
import unittest

from fixtest.base.message import BasicMessage


class TestBasicMessage(unittest.TestCase):
    # pylint: disable=missing-docstring

    def test_simple_basicmessage(self):
        """ Create a message and see if basic operations work.
        """
        mess = BasicMessage()
        self.assertEqual(0, len(mess))

        mess[19] = 111
        self.assertEqual(1, len(mess))
        self.assertEqual(111, mess[19])
        self.assertEqual(111, mess['19'])

    def test_field_ordering(self):
        """ Verify that the BasicMessage maintains the field ordering.
            That is the fields, when iterated, will appear in the
            order they were added.
        """
        mess = BasicMessage()
        mess[1] = 11
        mess[3] = 12
        mess[2] = 13

        self.assertEqual(3, len(mess))

        items = list(mess.items())
        self.assertEqual('1', items[0][0])
        self.assertEqual(11, items[0][1])
        self.assertEqual('3', items[1][0])
        self.assertEqual(12, items[1][1])
        self.assertEqual('2', items[2][0])
        self.assertEqual(13, items[2][1])

    def test_contains(self):
        """ Verify that contains accepts both integer and string keys.
        """
        mess = BasicMessage()
        mess[22] = 'abcd'

        self.assertTrue(22 in mess)
        self.assertTrue('22' in mess)
        self.assertFalse(33 in mess)
        self.assertFalse('33' in mess)

    def test_from_message(self):
        """ Verify that the message has the same fields as source message.
        """
        source_mess = BasicMessage()
        source_mess[23] = 2323
        source_mess[33] = 3333
        source_mess[11] = 1111

        new_mess = BasicMessage(source=source_mess)
        self.assertEqual(3, len(new_mess))

        items = list(new_mess.items())
        self.assertEqual('23', items[0][0])
        self.assertEqual(2323, items[0][1])
        self.assertEqual('33', items[1][0])
        self.assertEqual(3333, items[1][1])
        self.assertEqual('11', items[2][0])
        self.assertEqual(1111, items[2][1])

    def test_from_list(self):
        mess = BasicMessage(source=[(23, 2323), (33, 3333), (11, 1111)])
        self.assertEqual(3, len(mess))

        items = list(mess.items())
        self.assertEqual('23', items[0][0])
        self.assertEqual(2323, items[0][1])
        self.assertEqual('33', items[1][0])
        self.assertEqual(3333, items[1][1])
        self.assertEqual('11', items[2][0])
        self.assertEqual(1111, items[2][1])

    def test_from_ordereddict(self):
        new_dict = collections.OrderedDict()
        new_dict[22] = 99
        new_dict[21] = 101
        new_dict[20] = 2020

        mess = BasicMessage(source=new_dict)
        self.assertEqual(3, len(mess))

        items = list(mess.items())
        self.assertEqual('22', items[0][0])
        self.assertEqual(99, items[0][1])
        self.assertEqual('21', items[1][0])
        self.assertEqual(101, items[1][1])
        self.assertEqual('20', items[2][0])
        self.assertEqual(2020, items[2][1])

    def test_ordering(self):
        mess = BasicMessage()
        self.assertEqual(0, len(mess))

        mess[12] = 12
        mess[13] = 13
        self.assertEqual(2, len(mess))

        del mess[12]
        self.assertEqual(1, len(mess))
        self.assertTrue(13 in mess)
        self.assertTrue(12 not in mess)

        mess[12] = 14
        self.assertEqual(2, len(mess))

        items = list(mess.items())
        self.assertEqual('13', items[0][0])
        self.assertEqual(13, items[0][1])
        self.assertEqual('12', items[1][0])
        self.assertEqual(14, items[1][1])


if __name__ == '__main__':
    unittest.main()
