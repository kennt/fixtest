""" Utilities module

    Copyright (c) 2014-2022 Kenn Takara
    See LICENSE for details

"""

import datetime


def current_timestamp():
    """Return the current time as a string"""
    return datetime.datetime.now().strftime("%H:%M:%S.%f")


def format_log_line(header, text):
    """ Formats a single of line of text given a header and some text.
    """
    if header is None:
        return f"{current_timestamp()}: {text}"
    return f"{current_timestamp()}: {header}: {text}"


def log_text(log, header, text):
    """Write out the name/text to the specified log object"""
    log(format_log_line(header, text))
