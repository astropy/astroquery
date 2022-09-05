# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
gama
----
Access to GAMA (Galaxy And Mass Assembly) data, via the DR2 SQL query form.
http://www.gama-survey.org/dr3/query/

:author: James T. Allen <james.thomas.allen@gmail.com>
"""

from .core import GAMA, GAMAClass


__all__ = ["GAMA", "GAMAClass"]
