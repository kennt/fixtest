""" FIX parser class - responsible for FIX decoding

    Copyright (c) 2014 Kenn Takara
    See LICENSE for details

"""

from ..fix.message import FIXMessage


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

        The parser does not implement any timeout.  It is up to the
        protocol to determine if we are stuck in the middle of
        receiving a message.  If the parser is middle of receiving a
        message, the is_parsing attribute is set to True.

        Attributes:
            is_parsing: This is set to True if we are currently awaiting
                further data, in other words we have received a partial
                message.
            is_receiving_data: This is set to True if we are in the middle of
                processing a current buffer.
    """
    # pylint: disable=too-many-instance-attributes

    def __init__(self, receiver, **kwargs):
        """ FIXParser initialization

            Args:
                receiver: This is an observer that receives the message and
                    error notifications from the parser.  There are two
                    callbacks:
                        on_message_received(message)
                        on_error_received(error)
                header_fields: A list of header tags.  This only affects
                    the sending of the message. The order of the input
                    fields is not validated.
                binary_fields: A list of tags indicating binary fields.
                    Note that binary fields come in pairs.  The first
                    field contains the length of the data and the second
                    field contains the actual data.  The convention is that
                    the IDs are sequential.  For example, if the length field
                    is tag 123, then tag 124 contains the data.  Note that
                    only the first field should be included in this list.
                group_fields: A dictionary of fields that belong to a group.
                    The key is the group ID field that maps to a list of
                    IDs that belong to the group.
                max_length: Maximum length of a FIX message supported
                    (Default: 2048).
        """
        self.is_parsing = False

        self._receiver = receiver
        self._header_fields = kwargs.get('header_fields', [8, 9, 35, 49, 56])
        self._binary_fields = kwargs.get('binary_fields', list())
        self._group_fields = kwargs.get('group_fields', list())
        self._max_length = kwargs.get('max_length', 2048)

        self._buffer = b''
        self.is_receiving_data = False

        self._message = FIXMessage(header_fields=self._header_fields)

    def reset(self):
        """ Reset the protocol state so that it is ready to accept a
            new message.
        """
        self.is_parsing = False
        self._buffer = b''
        self._message = FIXMessage(header_fields=self._header_fields)

    def _parse_field(self, buf):
        """ Parses the 'id=value' field.  id must be a number.

            Returns: a tuple containing (id, value).

            Raises:
                FIXMessageParseError
        """
        # pylint: disable=no-self-use

        delim = buf.find('=')
        if delim == -1:
            raise FIXMessageParseError('Incorrect format: missing "="')

        tag_id = 0
        try:
            tag_id = int(buf[:delim])
        except ValueError:
            raise FIXMessageParseError('Incorrect format: ID must be a number')

        return (tag_id, buf[delim+1:])

    def on_data_received(self, data):
        """ Passes data to the parser.

            Once a message has been fully read in, the on_message callback
            is called.  When an error is detected in a message, on_error is
            called.

            Args:
                data: The binary data that has been received.  This may
                    either be a binary string or a single byte ot data.
        """
        if self.is_receiving_data is True:
            self._buffer += data
            return

        try:
            self.is_receiving_data = True
            self._buffer += data

            # Keep looping while we have unprocessed data
            # We start processing only once we have an entire field
            # (e.g. 'id=value') in the buffer, otherwise wait for more
            # data.
            while len(self._buffer) > 0 and self._buffer.find(b'\x01') != -1:
                # break up the field
                delim = self._buffer.find(b'\x01')
                field = self._buffer[:delim]
                self._buffer = self._buffer[delim+1:]

                tag_id, value = self._parse_field(field)

                # Is this the start of a message?
                if tag_id == 8:
                    if self.is_parsing:
                        raise FIXMessageParseError('unexpected tag: 8')
                    self.is_parsing = True
                elif not self.is_parsing:
                    raise FIXMessageParseError('message must start with tag 8')

                self._message[tag_id] = value

                # Is this the end of a message?
                if tag_id == 10:
                    self._receiver.on_message_received(self._message)
                    self.reset()

        except FIXMessageParseError, err:
            self.reset()
            self._receiver.on_error_received(err)
        finally:
            self.is_receiving_data = False
