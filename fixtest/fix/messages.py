""" Helper functions to create common FIX messages.

    Copyright (c) 2014 Kenn Takara
    See LICENSE for details

"""

from fixtest.fix.constants import FIX
from fixtest.fix.message import FIXMessage


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
