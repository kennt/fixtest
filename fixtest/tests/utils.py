""" test utilities module

    Copyright (c) 2014 Kenn Takara
    See LICENSE for details

"""

import collections


def to_fix(*args):
    """ Join a series of strings into a FIX binary message,
        a field list separated by \x01
    """
    return '\x01'.join(args) + '\x01'


def to_ordered_dict(v):
    """ Converts an unordered dict() into an orderedDict(), sorted
        by the key.
    """
    if isinstance(v, dict):
        return collections.OrderedDict(
            sorted(v.items(), key=lambda t: t[0]))
    elif isinstance(v, list):
        new_container = list()
        for item in v:
            new_container.append(to_ordered_dict(item))
        return new_container
    elif isinstance(v, tuple):
        return (v[0], to_ordered_dict(v[1]))
    else:
        return v
