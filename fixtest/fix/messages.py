""" Helper functions to create common FIX messages.

    Copyright (c) 2014 Kenn Takara
    See LICENSE for details

"""

import datetime

from fixtest.fix.constants import FIX
from fixtest.fix.message import FIXMessage
from fixtest.fix.utils import format_time


def logon_message(client):
    """ Generates a FIX logon message """
    return FIXMessage(source=[(35, FIX.LOGON),
                              (49, client.sender_compid),
                              (56, client.target_compid),
                              (98, 0),
                              (108, client.protocol.heartbeat)])


def logout_message(client):
    """ Generates a FIX logout message """
    return FIXMessage(source=[(35, FIX.LOGOUT),
                              (49, client.sender_compid),
                              (56, client.target_compid)])


def new_order_message(client, **kwargs):
    """ Generates a new order message.

        Arguments:

        Returns:

        Raises:
            ValueError
    """
    # Required parameters
    for sym in ['symbol', 'side', 'order_type']:
        if sym not in kwargs:
            raise ValueError("{0} must have a value".format(sym))

    # optional parameters
    extra_tags = kwargs.get('extra_tags', [])

    return FIXMessage(source=[
        (35, FIX.NEWORDER_SINGLE),
        (49, client.sender_compid),
        (56, client.target_compid),
        (11, client.get_next_orderid()),
        (21, '1'),  # handlInst
        (55, kwargs['symbol']),
        (54, kwargs['side']),
        (60, format_time(datetime.datetime.now())),
        (40, kwargs['order_type']),
        ] + extra_tags)


def execution_report(client, prev_message, **kwargs):
    """ Generates an execution report

        Arguments:
            client
            prev_message
            exec_trans_type:
            exec_type:
            ord_status:
            leaves_qty:
            cum_qty:
            avg_px:

        Returns:
        Raises:
            ValueError
    """
    # Required parameters
    for sym in ['exec_trans_type', 'exec_type', 'ord_status',
                'leaves_qty', 'cum_qty',
                'avg_px']:
        if sym not in kwargs:
            raise ValueError("{0} must have a value".format(sym))

    # optional parameters
    extra_tags = kwargs.get('extra_tags', [])
    exec_id = kwargs.get('exec_id', None) or client.get_next_orderid()

    message = FIXMessage(source=prev_message)
    message.update([
        (35, FIX.EXECUTION_REPORT),
        (49, client.sender_compid),
        (56, client.target_compid),
        (11, prev_message[11]),
        (37, client.get_next_orderid()),
        (17, exec_id),
        (20, kwargs['exec_trans_type']),
        (150, kwargs['exec_type']),
        (39, kwargs['ord_status']),
        (151, kwargs['leaves_qty']),
        (14, kwargs['cum_qty']),
        (6, kwargs['avg_px']),
        ] + extra_tags)
    return message
