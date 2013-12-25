# Licensed under a 3-clause BSD style license - see LICENSE.rst

"""
<Put Your Tool Name Here> 
------------------------------------------------------

:author: <your name> (<your email>) 
"""

# Make the URL of the server, timeout and other items configurable 
# See   for docs and examples on how to do this
# Below is a common use case

from astropy.config import ConfigurationItem

# Set the server mirrors to query
DUMMY_SERVER = ConfigurationItem('dummy_server',['http://dummy_server_mirror_1', 'http://dummy_server_mirror_2', 'http://dummy_server_mirror_n'], 'put a brief description of the item here')

# Set the timeout for connecting to the server
TIMEOUT = ConfigurationItem('timeout', n, 'default timeout for connecting to server')

# Now import your public class 
# Should probably have the same name as your module

from .core import DummyTool

__all__ = ['DummyTool']

