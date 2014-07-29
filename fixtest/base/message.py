""" Basic message container classes

    Copyright (c) 2014 Kenn Takara
    See LICENSE for details

"""

import collections


class BasicMessage(collections.MutableMapping):
    """ A BasicMessage is just a collection of (ID, VALUE) pairs.

        All IDs are converted into strings, this allows users of the
        BasicMessage to class to use integers or strings as keys.
        e.g. message[35] == message['35']

        If you iterate through the BasicMessage, the items will be
        returned in the order they were added.  This is important
        because the order of the fields is important to FIX.
    """
    def __init__(self, **kwargs):
        """ Initialization

            Args:
                source: copy over the fields from the source and
                    merge with this.  This can be a list of (ID, VALUE)
                    tuples or a BasicMessage().
        """
        self.store = collections.OrderedDict()

        if 'source' in kwargs:
            self.update(kwargs['source'])

    def __getitem__(self, key):
        return self.store[self.__keytransform__(key)]

    def __setitem__(self, key, value):
        self.store[self.__keytransform__(key)] = value

    def __delitem__(self, key):
        del self.store[self.__keytransform__(key)]

    def __iter__(self):
        return iter(self.store)

    def __len__(self):
        return len(self.store)

    def __keytransform__(self, key):
        """ Override this to enforce the type of key expected.
        """
        # pylint: disable=no-self-use
        return str(key)
