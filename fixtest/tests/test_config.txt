""" System configuration for the tests.
"""

ROLES = {
    'client': {},
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

CONNECTIONS = [
    {
        'name': 'client-FIX-gateway',
        'protocol': 'FIX',
        'host': 'localhost',
        'port': 9942,

        'client': 'FixClient',
        'gateway': 'FixServer',

        'market': 'ABC',
        'client-id': 'client1',
        'account-id': 'A',
        'acts-as-server': 'gateway',
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
