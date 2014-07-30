""" Utilities module

    Copyright (c) 2014 Kenn Takara
    See LICENSE for details

"""

import collections
import datetime


def flatten(container):
    """ Creates a list of tuples (k, v) from a dictionary
    """
    items = list()
    for k, v in container.items():
        if isinstance(v, collections.MutableMapping):
            items.append((k, len(v)))
            items.extend(flatten(v))
        else:
            items.append((k, v))
    return items


def current_timestamp():
    """Return the current time as a string"""
    return datetime.datetime.now().strftime("%H:%M:%S.%f")


def format_log_line(header, text):
    """ Formats a single of line of text given a header and some textself.
    """
    if header is None:
        return "{0}: {1}".format(current_timestamp(), text)
    else:
        return "{0}: {1}: {2}".format(current_timestamp(), header, text)


def log_text(log, header, text):
    """Write out the name/text to the specified log object"""
    log(format_log_line(header, text))
