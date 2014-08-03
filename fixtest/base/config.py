""" Configuration support

    Configuration here refers to a description of how the system and
    its connections are setup.

    There are two main components, the first one are the individual
    agents (or nodes) in the system.  The second are the connections
    (network links) in the system.

    We do not directly refer to the nodes in the sytem, but instead
    refer to them by the "roles" they play within the system.  These
    roles can be: "server", "client", "gateway", etc...  The node
    configurations provide information on these components.

    The link configurations describe the network configuration between
    two nodes.  Thus there is always a machine that acts as a receiver
    (e.g. the Server) and a machine that acts as a sender (the Client).
    Note that a machine with a certain role, say "Gateway" may act as
    a Client and a Server depending on the link confiugration.

    Additional sections may be added as needed.

    Each configuration object is a normal Python dict().  However, they
    can be sourced from anywhere.

    Copyright (c) 2014 Kenn Takara
    See LICENSE for details

"""

import copy


class Config(object):
    """ Base class for all configuration objects.  Usually the
        derived classes will setup the self._config dict().
    """
    def __init__(self):
        self._config = dict()

    def get_role(self, role_name):
        """ Returns the configuration for the given role.

            Args:
                role: The name of the role.

            Returns: A dict() that contains the configuration for the node.
        """
        return copy.deepcopy(self._config['ROLES'][role_name])

    def get_link(self, client_role, server_role, protocol_name='FIX'):
        """ Returns the configuration for the given link.
            The specific link is defined by:
            (1) the roles at the endpoints (ex. 'client', 'gateway')
            (2) which role is acting as the server (ex. 'gateway')
            (3) the protocol used (ex. 'FIX')

            Args:
                client_role: The role that is acting as the client, the
                    side that initiates the connection.
                server_role: The role that is acting as the server, the
                    side that waits for a connection.
                protocol_name: The protocol used betwen the two endpoints.

            Returns: A dict() that contains the configuration for the link.

            Raises: ValueError
        """
        for connection in self._config['CONNECTIONS']:
            if (client_role in connection and
                    server_role in connection and
                    connection['protocol'] == protocol_name and
                    connection['acts-as-server'] == server_role):
                return copy.deepcopy(connection)
        raise KeyError("Cannot find a matching configuration")

    def get_section(self, section_name):
        """ Returns the configuration section.

            Args:
                section_name:
        """
        return copy.deepcopy(self._config[section_name])

    def update(self, new_entries):
        """ Update the configuration with new data.

            Arguments:
                new_entries: The new data to add/update.
        """
        self._config.update(new_entries)


class FileConfig(Config):
    """ Provide the configuration from a file.
    """

    def __init__(self, file_name):
        """ Initialize from the given fileName

            Args:
                file_name:
        """
        super(FileConfig, self).__init__()
        execfile(file_name, globals(), self._config)


class DictConfig(Config):
    """ Provide the configuration from a pre-existing dictionary.
    """
    def __init__(self, initial_config):
        """ Dictionary-based configuration

            Args:
                initial_config
        """
        super(DictConfig, self).__init__()
        self._config = initial_config
