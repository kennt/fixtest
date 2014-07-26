""" FIX parser class - responsible for FIX decoding

    Copyright (c) 2014 Kenn Takara
    See LICENSE for details

"""


class FIXMessageParseError(ValueError):
    """ Exception: FIX Message is not in proper FIX format. """
    def __init__(self, message):
        super(FIXMessageParseError, self).__init__()
        self.message = message

    def __str__(self):
        return self.message


class FIXMessageLengthExceededError(ValueError):
    """ Exception: FIX message too long. """


class FIXParser(object):
    """ Implements the core decoding of FIX messages.  The encoding
        portion is taken up by the FIXMessage itself.

        This class is responsible for the decoding of FIX messages.
        It does not implement any behavior aside from some message
        validation (length checking, checksum verification, etc..).
        Heartbeat/TestRequest processing are not performed here.

        Attributes:
    """
    # pylint: disable=too-many-instance-attributes

    def __init__(self, on_message, on_error, **kwargs):
        """ FIXParser initialization

            Args:
                on_message: A callback.  This function is called when a
                    full message has been received.
                on_error: A callback.  This function is called when an error
                    has been detected while processing data.
                header_fields: A list of header tags.
                binary_fields: A list of tags indicating binary fields.
                    Note that binary fields come in pairs.  The first
                    field contains the length of the data and the second
                    field contains the actual data.  The convention is that
                    the IDs are sequential.  For example, if the length field
                    is tag 123, then tag 124 contains the data.  Note that
                    only the first field should be included in this list.
                group_fields: A list of tuples (groupID, taglist) indicating
                    the list of group fields supported.
                max_length: Maximum length of a FIX message supported
                    (Default: 2048).
        """
        self._on_message = on_message
        self._on_error = on_error
        self._header_fields = kwargs.get('header_fields', [8, 9, 35, 49, 56])
        self._binary_fields = kwargs.get('binary_fields', list())
        self._group_fields = kwargs.get('group_fields', list())
        self._max_length = kwargs.get('max_length', 2048)

        self._buffer = b''
        self._receiving_data = False

    def reset(self):
        """ Reset the protocol state so that it is ready to accept a
            new message.
        """
        self._buffer = b''
        self._receiving_data = False

    def on_data_received(self, data):
        """ Passes data to the parser.

            Once a message has been fully read in, the on_message callback
            is called.  When an error is detected in a message, on_error is
            called.

            Args:
                data: The binary data that has been received.
        """
        if self._receiving_data is True:
            self._buffer += data
            return

        try:
            self._receiving_data = True
            self._buffer += data

        finally:
            self._receiving_data = False
