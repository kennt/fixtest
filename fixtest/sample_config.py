""" Sample system configuration file.

    Also documents some of the expected fields (especially for FIX).

    There are three main sections: ROLES, CONNECTIONS, and others.

    ROLES: Every node (or endpoint) takes on a particular 'role'.  Such as
        a client or a server.  Note that a process can be a client for one
        connection and may act as a server for another connection.

        This section contains information that are particular to the
        endpoint.  For instance, if there is a separate way of interfacing
        with the system, then that would be specified here.

    CONNECTIONS: This describes the connection between two endpoints.

        Each connection (or link) is uniquely distinguished by the
        two roles involved (e.g. client-server, client-gateway,
        server-gateway, etc...), the protocol used (e.g. FIX), and
        which role acts as the server (that is which side is waiting
        for a connection to be initiated).

    other: other sections may be added (and accessed) as necessary.
"""

# ROLES
#   Roles contain endpoint information.  The information stored here
#   is usually very specific to the particular system requirements.
#
ROLES = {
    'client': {},
    'gateway': {},
    'exchange': {},
}


FIX_4_2 = {
    # The values here are examples only.  They should be customized
    # for your particular needs/implementation.
    'protocol_version': 'FIX.4.2',
    'header_fields': [8, 9],
    'binary_fields': [],
    'required_fields': [8, 9, 10, 35],
    'group_fields': {},
    'max_length': 2048,
}

# CONNECTIONS
#
#   This section contains things like: connection information, protocol
#   information, FIX connection information, and sometimes
#   other test information as needed.
#
#   Connection information
#   ======================
#   name: A descriptive name describing this connection.
#   protocol: The protocol used for this connection.  This is mainly
#       used to distinguish connection configurations.
#   host: The IP address/DNS name used by the server.
#   port: The port number used by the server.
#   <client-role-name>: This is the name of the role that acts as the
#       client in the connection.  The value for this is a descriptive
#       string.  For FIX, this becomes the senderCompID when the client
#       sends data and the targetCompID when the client receives data.
#   <server-role-name>: This is the name of the role that acts as the
#       server in the connection.  The value for this is a descriptive
#       string.  For FIX, this becomes the targetCompID when the server
#       receives data and the senderCompID when the sender sends data.
#   acts-as-server: This is the name of the role that acts as the server
#       in this connection.  That is, the role that waits for a connectoin.
#       This name must be either <client-role-name> or <server-role-name>.
#
#   FIX protocol information:
#   ========================
#   protocol_version:   This is the FIX version that is sent and is expected
#       by the FIX protocol implementation.  This is the string that is in
#       the BeginString(8) field.
#   required_fields: A list of fields that are required to be in the
#       message, both on sending and receiving.  This is checked for ALL
#       messages, both data and administrative messages.  The tag must exist
#       in the message and must not be blank.
#   header_fields: A list of header tags.  This only affects
#       the sending of the message. The order of the input
#       fields is not validated. (Default: [8, 9, 35, 49, 56])
#   binary_fields: The list of FIX binary fields supported
#       or needed by this link (Default: None).
#       Note that binary fields come in pairs.  The first
#       field contains the length of the data and the second
#       field contains the actual data.  The convention is that
#       the IDs are sequential.  For example, if the length
#       field is tag 123, then tag 124 contains the data.
#       Note that only the first field should be included
#       in this list.
#   group_fields: A dictionary of fields that belong
#       to a group. The key is the group ID field that maps
#       to a list of IDs that belong to the group.
#   max_length: The maximum length of message (Default: 2048)
#
#   FIX connection information:
#   ==========================
#   heartbeat: The heartbeat interval (in secs).  IF this
#       is set to -1, then the heartbeat is not sent.
#   send_seqno: This is the starting seqno.
#   orderid_no: This is the starting order no.
#
#   Calculate fields (do NOT set these manually)
#   ============================================
#   sender_compid: The sender endpoint ID.
#   target_compid: The target endpoint ID.


CONNECTIONS = [
    {
        # connection information
        'name': 'client-FIX-gateway',
        'protocol': 'FIX',
        'host': 'localhost',
        'port': 8080,

        'client': 'FixClient',
        'gateway': 'FixGateway',
        'acts-as-server': 'gateway',

        # other information used by the tests
        'market': 'ABC',
        'client-id': 'client1',
        'account-id': 'A',

        # protocol information
        'protocol_version': FIX_4_2['protocol_version'],
        'binary_fields': FIX_4_2['binary_fields'],
        'header_fields': FIX_4_2['header_fields'],
        'required_fields': FIX_4_2['required_fields'],
        'group_fields': FIX_4_2['group_fields'],
    },
]
