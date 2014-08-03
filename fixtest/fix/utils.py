""" Utilities module

    Copyright (c) 2014 Kenn Takara
    See LICENSE for details

"""

import collections

from fixtest.base.utils import format_log_line
from fixtest.fix.constants import FIX


def flatten(container):
    """ Creates a list of tuples (k, v) from a dictionary

        This is FIX specific.  If a key maps to a container, say
        (k: v) where v is another dict(), then the item (k, len(v))
        is added to the list of items, followed by
        (k, v[0]), (k, v[1]), ...
    """
    items = list()
    for k, v in container.items():
        if isinstance(v, collections.MutableMapping):
            items.append((k, len(v)))
            items.extend(flatten(v))
        else:
            items.append((k, v))
    return items


def format_time(input_datetime):
    """ Formats the datetime according to the FIX spec.

        Args:
            input: a datetime

        Returns:
            A string that can be sent in a FIX message.
    """
    return input_datetime.strftime("%Y%m%d-%H:%M:%S")


def format_message(message):
    """ Formats a FIX message for easier reading """
    return ', '.join(["{0}={1}".format(k, v) for k, v in flatten(message)])


def log_message(log, header, message, text):
    """ Logs and formats the message (with the header and text)
    """
    exectype = ''
    if 150 in message:
        exectype = ' : (' + FIX.find_exectype(message[150]) + ')'

    log(format_log_line(header, text) + '\n' +
        '    ' + FIX.find_msgtype(message[35]) + exectype +
        ' : ' + format_message(message) + '\n')
