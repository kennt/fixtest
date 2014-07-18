""" FIX message container classes

    Copyright (c) 2014 Kenn Takara
    See LICENSE for details

"""

from cStringIO import StringIO
import struct

from ..base.message import BasicMessage
from ..fix.constants import FIX


def checksum(data):
    """ Calculates the checksum of the message according to FIX.

        This does not do any filtering of the data, so do not
        calculate this with field 10 included.
    """
    chksum = 0
    for c in data:
        chksum = (chksum + struct.unpack('B', c)[0]) % 256

    return chksum


def _single_tag(tag, value):
    """ Returns a string in the form of "tag=value\x01"
    """
    # Note that we are filtering out non-numeric characters from
    # the tag IDs.  For nested groups, we append on non-numeric
    # characters to disambiguate the tags (we are using a dict() to
    # store the fields).
    return (''.join([c for c in str(tag) if c.isdigit()]) +
            '=' + str(value) + b'\x01')


def _write_single_tag(output, tag, value):
    """ Writes a single tag. Value must not be a container.

        This is a FIX-formatted message, so this assumes that the
        key is a numeric string, that is only digits are allowed.

        Args:
            output:
            tag:
            value:
    """
    output.write(_single_tag(tag, value))


def _write_tag(output, tag, value):
    """ Writes a tag to the output. The value may be hiearchical.

        Args:
            output:
            tag: The ID portion.
            value: The value portion.  This may be a nested group.
    """
    if hasattr(value, '__iter__'):
        # write out the number of subgroups
        _write_single_tag(output, tag, len(value))
        for subgroup in value:
            for k, v in subgroup.iteritems():
                _write_tag(output, k, v)
    else:
        _write_single_tag(output, tag, value)


class FIXMessage(BasicMessage):
    """ Adds support for some basic FIX-specific functionality on top of
        the BasicMessage class.

        Note that FIX requires a specific field ordering.  This class
        provides support for FIX-like protocols, but not necessarily
        for a specific version.
    """

    def __init__(self, **kwargs):
        """ Initialization

            Args:
                source: A source message.  This will be used to initialize
                    the message.
                required: A list of required tag IDs.  Sequence ordering
                    matters.  (Default: [8, 9, 35, 49, 56])
                    8 = BeginString
                    9 = BodyLength
                    35 = MsgType
                    49 = SenderCompID
                    56 = TargetCompID
        """
        super(FIXMessage, self).__init__()

        # Preinsert required header fields
        required = kwargs.get('required', [8, 9, 35, 49, 56])
        for tag in required:
            self[tag] = ''

        if 'source' in kwargs:
            self.update(kwargs['source'])

    def msg_type(self):
        """ Returns the MessageType field (tag 35) of the message.

            Returns: a string containing the value of the tag 35 field.
        """
        return self[35]

    def to_binary(self, **kwargs):
        """ Converts the message into the on-the-wire format.

            This will prepare the message for sending by updating
            the body length (9) and checksum (10) fields.

            Args:
                include: A list of tags to explicitly include, tags not
                    in the list are not included. If this is not set,
                    then the default is to include all tags.
                exclude: A list of tags to explicitly exclude, tags not
                    in the list are included.  If this is not set, the
                    default is to not exclude any tags.

            Returns:
                A binary string containing the message in the
                FIX on-the-wire format.
        """
        includes = {str(k): True for k in kwargs['include']} \
            if 'include' in kwargs else None
        excludes = {str(k): True for k in kwargs['exclude']} \
            if 'exclude' in kwargs else None

        output = StringIO()

        for k, v in self.items():
            if includes is not None and k not in includes:
                continue
            if excludes is not None and k in excludes:
                continue

            # Generate the binary without these fields
            if k == str(8) or k == str(9) or k == str(FIX.CHECKSUM):
                continue

            # write a tag out, this may be a grouped value
            _write_tag(output, k, v)

        message = output.getvalue()

        # prepend 8 (BeginString) and 9 (BodyLength)
        self[9] = len(message)
        message = _single_tag(8, self[8]) + _single_tag(9, self[9]) + message

        # calc and append the 10 (CheckSum)
        if 10 in self:
            del self[10]
        self[10] = '%03d' % checksum(message)
        return message + _single_tag(10, self[10])

    def verify(self, tags=None, exists=None, not_exists=None):
        """ Checks for the existence/value of tags/values.

            Args:
                tags: A list of (tag, value) pairs.  The message
                    is searched for the tag and then checked to see if
                    the value is equal.
                exists: A list of tag ids.  The message is checked
                    for the existence of these tags (the value doesn't
                    matter).
                not_exists: A list of tag ids.  The message is checked
                    to see that it does NOT contain these tags.

            Returns: True if the conditions are satisifed.
                False otherwise.
        """
        tags = tags or list()
        exists = exists or list()
        not_exists = exists or list()

        for tag in tags:
            if tag[0] not in self or str(self[tag[0]]) != str(tag[1]):
                return False

        for tag in exists:
            if tag not in self:
                return False

        for tag in not_exists:
            if tag in self:
                return False

        return True
