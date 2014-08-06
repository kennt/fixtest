# FIXTest - FIX Protocol Test tool
The purpose of this tool is to provide a way to test networking components
using the FIX level at the system level, not unit test.  Initially, I
wanted a way to reproduce and document specific test cases so that I
could perform regression tests at a later date.

This tool provides a way of creating test cases that can act as FIX clients
or as FIX servers.  But this is not a simulator, the test case author is
responsible for generating the actual messages and checking their correctness.

## What this is not
* This is not a simulator. This tool was made to help document specific
test cases (thus ensuring that I could repro and verify a test case).
* This is not meant for unit testing, but component level testing.
* This currently only supports FIX-based protocols.  In theory this 
could support other protocols, but I haven't tried to make it more protocol agnostic.

## What is supported
* Groups
* Binary fields
* TestRequest/Heartbeat processing

## How to use
1. Write a configuration file
2. Write a testcase
3. Run the testcase

### Configuration
The configuration is gathered from a config file.  The default name for the
file is my_config.py.  A full description of the contents of the file may be
found in sample_config.py

Here is a sample configuration file.
```python

ROLES = {
    'client': {},
    'test-server': {},
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
        'port': 9000,

        'client': 'FixClient',
        'test-server': 'FixServer',
        'acts-as-server': 'test-server',

        # protocol information
        'protocol_version': FIX_4_2['protocol_version'],
        'binary_fields': FIX_4_2['binary_fields'],
        'header_fields': FIX_4_2['header_fields'],
        'required_fields': FIX_4_2['required_fields'],
        'group_fields': FIX_4_2['group_fields'],
    },
]

```


### Sample test code
### Running the test

