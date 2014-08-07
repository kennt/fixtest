FIXTest - FIX Protocol Test tool
================================
The purpose of this tool is to provide a way to test networking components
using the FIX level at the system level, not unit test.  Initially, I
wanted a way to reproduce and document specific test cases so that I
could perform regression tests at a later date.

This tool provides a way of creating test cases that can act as FIX clients
or as FIX servers.  But this is not a simulator, the test case author is
responsible for generating the actual messages and checking their correctness.

