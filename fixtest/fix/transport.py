""" FIX transport class - responsible for the interface
    between the protocol and the actual Twisted transport.

    Copyright (c) 2014 Kenn Takara
    See LICENSE for details

"""

from twisted.internet import protocol


class FIXTransport(protocol.Protocol):
    """ This class is the interface between the FIXProtocol and
        the actual Twisted transport.
    """
    def __init__(self, receiver):
        self.receiver = receiver

    def dataReceived(self, data):
        """ This is the callback from Twisted.
        """
        self.protocol.on_data_received(data)

    def send_message(self, data):
        """ This is the callback from the protocol.  Send the
            message onto through the transport.
        """
        self.receiver.send_message(data)
