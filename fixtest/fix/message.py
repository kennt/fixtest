""" FIX message container classes

    Copyright (c) 2014 Kenn Takara
    See LICENSE for details

"""

from cStringIO import StringIO
import struct

from ..base.message import BasicMessage


class FIXMessage(BasicMessage):
    """ Adds support for some basic FIX-specific functionality on top of
        the BasicMessage class.

        Note that FIX requires a specific field ordering.  This class
        provides support for FIX-like protocols, but not necessarily
        for a specific version.
    """
    def __init__(self, **kwargs):
        super(FIXMessage, self).__init__(**kwargs)

    def msg_type(self):
        """ Returns the MessageType field (tag 35) of the message.

            Returns: a string containing the value of the tag 35 field.
        """
        return self[35]

    def _write_single_tag(self, output, tag, value):
        """ Writes a single tag. Value must not be a container.

            This is a FIX-formatted message, so this assumes that the
            key is a numeric string, that is only digits are allowed.

            Args:
                output:
                tag:
                value:
        """
        # pylint: disable=no-self-use
        output.write(''.join([c for c in str(tag) if c.isdigit()]) +
                     '=' + str(value) + b'\x01')

    def _write_tag(self, output, tag, value):
        """ Writes a tag to the output. The value may be hiearchical.

            Args:
                output:
                tag: The ID portion.
                value: The value portion.  This may be a nested group.
        """
        if hasattr(value, '__iter__'):
            # write out the number of subgroups
            self._write_single_tag(output, tag, len(value))
            for subgroup in value:
                for k, v in subgroup.iteritems():
                    self._write_tag(output, k, v)
        else:
            self._write_single_tag(output, tag, value)

    def to_binary(self, **kwargs):
        """ Converts the message into the on-the-wire format.

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

            # write a tag out, this may be a grouped value
            self._write_tag(output, k, v)

        return output.getvalue()

    def update_body_lengh(self):
        """ Updates the body-length field (tag 9) of the message.

            Fields 8, 9, 10 are not included when calculating the
            length of the message (according to the FIX spec).
        """
        self[9] = len(self.to_binary(exclude=[8, 9, 10]))

    def update_checksum(self):
        """ Updates the checksum field (tag 10) of the message.

            The checksum is calculated and field 10 is updated.
            Field 10 is then reappended to the end of the message,
            the FIX spec requires that the checksum (field 10) is
            always at the end of the message.
        """
        if 10 in self:
            del self[10]

        data = self.to_binary(exclude=[10])
        chksum = 0
        for c in data:
            chksum = (chksum + struct.unpack('B', c)[0]) % 256

        self[10] = '%03d' % chksum

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
