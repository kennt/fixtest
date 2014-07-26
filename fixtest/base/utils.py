""" Utilities module

    Copyright (c) 2014 Kenn Takara
    See LICENSE for details

"""

import datetime


def current_timestamp():
    """Return the current time as a string"""
    return datetime.datetime.now().strftime("%H:%M:%S.%f")


def log_text(log, name, text):
    """Write out the name/text to the specified log object"""
    if name is None:
        return log("{0}: {1}".format(current_timestamp(), text))
    else:
        return log("{0}: {1}: {2}".format(current_timestamp(), name, text))
