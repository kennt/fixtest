""" FIX message container classes

    Copyright (c) 2014-2022 Kenn Takara
    See LICENSE for details

"""

from io import BytesIO

from fixtest.base.message import BasicMessage


def checksum(data, starting_checksum=0):
    """ Calculates the checksum of the binary message according to FIX.

        This does not do any filtering of the data, so do not
        calculate this with field 10 included.
    """
    chksum = starting_checksum
    for bval in data:
        chksum = (chksum + bval) % 256

    return chksum


def _single_field(tag, value):
    """ Returns a byte string in the form of "tag=value\x01"
    """
    iobuf = BytesIO()

    iobuf.write(str.encode(f"{tag}="))
    if isinstance(value, bytes):
        iobuf.write(value)
    else:
        iobuf.write(str(value).encode('latin-1'))
    iobuf.write(b'\x01')
    return iobuf.getvalue()


def _write_single_field(output, tag, value):
    """ Writes a single field. Value must not be a container.

        This is a FIX-formatted message, so this assumes that the
        key is a numeric string, that is only digits are allowed.

        Args:
            output:
            tag:
            value:
    """
    output.write(_single_field(tag, value))


def _write_field(output, tag, value):
    """ Writes a field to the output. The value may be hiearchical.

        Args:
            output:
            tag: The ID portion.
            value: The value portion.  This may be a nested group.
    """
    if isinstance(value, list):
        # write out the number of subgroups
        _write_single_field(output, tag, len(value))
        for subgroup in value:
            for key, val in subgroup.items():
                _write_field(output, key, val)
    else:
        _write_single_field(output, tag, value)


class FIXMessage(BasicMessage):
    """ Adds support for some basic FIX-specific functionality on top of
        the BasicMessage class.

        Note that FIX requires a specific field ordering.  This class
        provides support for FIX-like protocols, but not necessarily
        for a specific version.

        A FIX field is composed of (tag, value) pairs.  A tag is a
        numeric positive integer field.  The value is a string.
    """

    def __init__(self, **kwargs):
        """ Initialization

            Args:
                source: A source message.  This will be used to initialize
                    the message.
                header_fields: A list of header tags.
                    Sequence ordering matters.  (Default: [8, 9, 35, 49, 56])
                    8 = BeginString
                    9 = BodyLength
                    35 = MsgType
                    49 = SenderCompID
                    56 = TargetCompID
                    This setting only affects to_binary(), the input order
                    is not validated here.
        """
        super().__init__()

        # Preinsert header fields
        header = kwargs.get('header_fields', [8, 9, 35, 49, 56])
        for tag in header:
            self[tag] = ''

        if 'source' in kwargs:
            self.update(kwargs['source'])

    def __keytransform__(self, key):
        """ Override this to enforce the type of key expected.

            FIX only expects purely numeric keys.
        """
        return int(key)

    def msg_type(self):
        """ Returns the MessageType field (tag 35) of the message.

            Returns: a string containing the value of the tag 35 field.
        """
        if isinstance(self[35], bytes):
            return self[35].decode()
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
        includes = {int(k): True for k in kwargs['include']} \
            if 'include' in kwargs else {}
        excludes = {int(k): True for k in kwargs['exclude']} \
            if 'exclude' in kwargs else {}

        output = BytesIO()

        for key, val in self.items():
            if len(includes) > 0 and key not in includes:
                continue
            if len(excludes) > 0 and key in excludes:
                continue

            # Generate the binary without these fields
            if key in {8, 9, 10}:
                continue

            # write a field out, this may be a grouped value
            _write_field(output, key, val)

        mess = output.getvalue()

        # prepend 8 (BeginString) and 9 (BodyLength)
        # Note that 8 and 9 are the minimal set of required fields
        self[9] = str(len(mess))
        mess = _single_field(8, self[8]) + _single_field(9, self[9]) + mess

        # calc and append the 10 (CheckSum)
        if 10 in self:
            del self[10]
        self[10] = f'{checksum(mess):03d}'
        return mess + _single_field(10, self[10])

    def verify(self, fields=None, exists=None, not_exists=None):
        """ Checks for the existence/value of tags/values.

            Args:
                fields: A list of (tag, value) pairs.  The message
                    is searched for the tag and then checked to see if
                    the value is equal.
                exists: A list of tags.  The message is checked
                    for the existence of these tags (the value doesn't
                    matter).
                not_exists: A list of tags.  The message is checked
                    to see that it does NOT contain these tags.

            Returns: True if the conditions are satisifed.
                False otherwise.
        """

        fields = fields or []
        exists = exists or []
        not_exists = not_exists or []

        for field in fields:
            if field[0] not in self:
                return False

            if self[field[0]] != field[1]:
                return False

        for tag in exists:
            if tag not in self:
                return False

        for tag in not_exists:
            if tag in self:
                return False

        return True
