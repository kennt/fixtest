""" Utilities module

    Copyright (c) 2014 Kenn Takara
    See LICENSE for details

"""

from ..base.utils import format_log_line, flatten
from ..fix.constants import FIX


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
