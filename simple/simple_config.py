""" Simple configuration used for testing.

    Copyright (c) 2014 Kenn Takara
    See LICENSE for details

"""

ROLES = {
    'client': {},
    'test-server': {},
    'gateway': {
        'admin-address': 'localhost',
        'admin-port': 19400,
    },
    'exchange': {
        'admin-address': 'localhost',
        'admin-port': 19404,
    },
    'cmd': {
        'executable-path': '/home/kenn/bin/cmd',
    },
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

CONNECTIONS = [
    {
        # connection information
        'name': 'client-FIX-test-server',
        'protocol': 'FIX',
        'host': 'localhost',
        'port': 9940,

        'client': 'FixClient',
        'test-server': 'FixServer',
        'acts-as-server': 'test-server',

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


# Indexed by 'market'
SECURITIES = {
    'ABC': [
        {'symbol': 'BBB', 'exchange': 'A'},
        {'symbol': 'CCC', 'exchange': 'A'},
        {'symbol': 'DDD', 'exchange': 'A'},
    ],
}
