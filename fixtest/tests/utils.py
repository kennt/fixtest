""" test utilities module

    Copyright (c) 2014-2022 Kenn Takara
    See LICENSE for details

"""

import collections


def to_fix(*args):
    """ Join a series of strings into a FIX binary message,
        a field list separated by \x01
    """
    return b'\x01'.join([x.encode('latin-1') for x in args]) + b'\x01'


def to_ordered_dict(val):
    """ Converts an unordered dict() into an orderedDict(), sorted
        by the key.
    """
    if isinstance(val, dict):
        return collections.OrderedDict(
            sorted(val.items(), key=lambda t: t[0]))
    if isinstance(val, list):
        new_container = []
        for item in val:
            new_container.append(to_ordered_dict(item))
        return new_container
    if isinstance(val, tuple):
        return (val[0], to_ordered_dict(val[1]))
    return val
