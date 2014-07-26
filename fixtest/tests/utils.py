""" test utilities module

    Copyright (c) 2014 Kenn Takara
    See LICENSE for details

"""


def to_fix(*args):
    """ Join a series of strings into a FIX binary message,
        a field list separated by \x01
    """
    return '\x01'.join(args) + '\x01'
