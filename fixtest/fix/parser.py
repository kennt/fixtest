""" FIX parser class - responsible for FIX decoding

    Copyright (c) 2014 Kenn Takara
    See LICENSE for details

"""

import collections
import logging

from fixtest.base.utils import log_text
from fixtest.fix.message import FIXMessage, checksum


class FIXParserError(ValueError):
    """ Exception: FIX Message is not in proper FIX format. """
    def __init__(self, message):
        super(FIXParserError, self).__init__()
        self.message = message

    def __str__(self):
        return self.message


class FIXLengthTooLongError(ValueError):
    """ Exception: FIX message too long. """
    def __init__(self, message):
        super(FIXLengthTooLongError, self).__init__()
        self.message = message

    def __str__(self):
        return self.message


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
                    IDs that belong to the group.  When specifying the
                    field list for a group, include BOTH fields of a
                    binary field.
                max_length: Maximum length of a FIX message supported
                    (Default: 2048).
                debug: Set to True for more debugging output
        """
        self.is_parsing = False

        self._receiver = receiver
        self._header_fields = kwargs.get('header_fields', [8, 9, 35, 49, 56])
        self._binary_fields = kwargs.get('binary_fields', list())
        self._group_fields = kwargs.get('group_fields', list())
        self._max_length = kwargs.get('max_length', 2048)
        self._debug = kwargs.get('debug', False)

        self._buffer = b''
        self.is_receiving_data = False

        self._message = FIXMessage(header_fields=self._header_fields)
        self._checksum = 0
        self._message_length = 0

        # used for binary field processing
        self._binary_length = -1
        self._binary_tag = 0

        # used for groups processing
        self._level_stack = list()

        self._logger = logging.getLogger(__name__)

    def reset(self, flush_buffer=False):
        """ Reset the protocol state so that it is ready to accept a
            new message.
        """
        self.is_parsing = False
        self._message = FIXMessage(header_fields=self._header_fields)
        self._checksum = 0
        self._message_length = 0

        # used for binary field processing
        self._binary_length = -1
        self._binary_tag = 0

        # used for groups processing
        self._level_stack = list()

        if flush_buffer:
            self._buffer = b''

    def _parse_field(self, buf):
        """ Parses the 'id=value' field.  id must be a number.

            Returns: a tuple containing (id, value).

            Raises:
                FIXParserError
        """
        # pylint: disable=no-self-use

        delim = buf.find('=')
        if delim == -1:
            raise FIXParserError('Incorrect format: missing "="')

        tag_id = 0
        try:
            tag_id = int(buf[:delim])
        except ValueError:
            raise FIXParserError('Incorrect format: ID:' + buf[:delim])

        return (tag_id, buf[delim+1:])

    def _update_length(self, field, tag_id, value):
        """ Update the message length calculations """
        # pylint: disable=unused-argument
        if tag_id not in {8, 9, 10}:
            self._message_length += len(field) + 1
        if self._message_length >= self._max_length:
            raise FIXLengthTooLongError(
                'message too long: {0}'.format(self._message_length))

    def _update_checksum(self, field, tag_id, value):
        """ Update the message checksum calculations """
        # pylint: disable=unused-argument
        if tag_id != 10:
            self._checksum = checksum(field, self._checksum) + 1

    def _update_binary(self, field, tag_id, value):
        """ Update the binary field processing internals """
        # Are we processing a binary tag?
        if self._binary_tag == 0:
            if tag_id in self._binary_fields:
                self._binary_length = len(str(tag_id + 1)) + int(value)
                if self._binary_length > self._max_length:
                    raise FIXLengthTooLongError(
                        'binary field too long: {0} ref:{1}'.format(
                            self._binary_length, tag_id))
                self._binary_tag = tag_id
            else:
                self._binary_length = -1
        else:
            # Is this the wrong tag?
            if tag_id != (self._binary_tag + 1):
                raise FIXParserError(
                    'expected binary tag {0} found {1}'.format(
                        self._binary_tag + 1, tag_id))
            if len(field) != self._binary_length + 1:
                raise FIXParserError(
                    'binary length: expected {0} found {1}'.format(
                        self._binary_length + 1, len(field)))
            self._binary_tag = 0
            self._binary_length = -1

    def _update_field(self, tag_id, value):
        """ Update the value of the field

            Need to change the level of the container due to the
            grouping aspects.
        """
        if tag_id in self._group_fields:
            # start a new level, an individual group doesn't
            # exist since we haven't read any information in yet.
            self._level_stack.append({
                'tag_id': tag_id,
                'list': list(),
                'group': None,
                })

        elif len(self._level_stack) == 0:
            # We are at the top of the message
            self._message[tag_id] = value

        elif tag_id in self._group_fields[self._level_stack[-1]['tag_id']]:
            # We are within a group and the field is in the list of tags
            # for this group
            level = self._level_stack[-1]
            group = level['group']
            if group is None or tag_id in group:
                # Create a new group if there is no current group
                # or if this key already exists within the group
                group = collections.OrderedDict()
                level['list'].append(group)
                level['group'] = group
            group[tag_id] = value

        else:
            # we are in a grouping, but we have a tag_id that doesn't
            # belong, so need to pop the stack off
            level = self._level_stack.pop()  # this is the current level

            while len(self._level_stack) > 0:
                # Add the current group to it's parent grouping
                parent_level = self._level_stack[-1]
                parent_level['group'][level['tag_id']] = level['list']

                level = parent_level
                if tag_id in self._group_fields[level['tag_id']]:
                    break
                self._level_stack.pop()

            if len(self._level_stack) == 0:
                self._message[level['tag_id']] = level['list']

            self._update_field(tag_id, value)

    def on_data_received(self, data):
        """ Passes data to the parser.

            Once a message has been fully read in, the on_message callback
            is called.  When an error is detected in a message, on_error is
            called.

            Args:
                data: The binary data that has been received.  This may
                    either be a binary string or a single byte ot data.
        """
        # pylint: disable=too-many-branches,too-many-statements

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
            # The problem with the current approach is that if there is a
            # binary field with an incorrect length, we may read past
            # the end of the message.
            # BUGBUG: Need to fix this. A quick hack may be to
            # try to peek to see what the tag id is and do something
            # with that.  On the other hand this may just be a problem
            # with the protocol (should probably specify a maximum
            # allowable length of a binary field as a sanity check)
            while (len(self._buffer) > 0 and
                    self._buffer.find(b'\x01', self._binary_length + 1) != -1):

                # Need to make sure that we have the entire binary field
                # before continuing the processing
                if (self._binary_length > 0 and
                        len(self._buffer) < self._binary_length):
                    break

                # break up the field
                delim = self._buffer.find(b'\x01', self._binary_length + 1)
                field = self._buffer[:delim]
                self._buffer = self._buffer[delim+1:]

                tag_id, value = self._parse_field(field)

                # Is this the start of a message?
                if tag_id == 8:
                    if self.is_parsing:
                        raise FIXParserError('unexpected tag: 8')
                    self.is_parsing = True
                elif not self.is_parsing:
                    raise FIXParserError('message must start with tag 8')

                if self._debug:
                    log_text(self._logger.debug, None,
                             "tag {0} = {1}".format(tag_id, repr(value)))

                self._update_length(field, tag_id, value)
                self._update_checksum(field, tag_id, value)
                self._update_binary(field, tag_id, value)

                # The tag value gets assigned here. Due to grouping
                # the container where the update takes place gets
                # changed
                # self._message[tag_id] = value
                self._update_field(tag_id, value)

                # Is this the end of a message?
                if tag_id == 10:
                    self._receiver.on_message_received(self._message,
                                                       self._message_length,
                                                       self._checksum)
                    self.reset()

        except FIXLengthTooLongError, err:
            self.reset(flush_buffer=True)
            self._receiver.on_error_received(err)
        except FIXParserError, err:
            self.reset(flush_buffer=True)
            self._receiver.on_error_received(err)
        finally:
            self.is_receiving_data = False
