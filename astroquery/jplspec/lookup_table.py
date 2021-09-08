# Licensed under a 3-clause BSD style license - see LICENSE.rst
import re


class Lookuptable(dict):

    def find(self, s, flags):
        """
        Search dictionary keys for a regex match to string s

        Parameters
        ----------
        s : str
            String to compile as a regular expression
            Can be entered non-specific for broader results
            ('H2O' yields 'H2O' but will also yield 'HCCCH2OD')
            or as the specific desired regular expression for
            catered results, for example: ('H20$' yields only 'H2O')

        flags : int
            Regular expression flags.

        Returns
        -------
        The list of values corresponding to the matches

        """

        R = re.compile(s, flags)

        out = {}

        for k, v in self.items():
            match = R.search(str(k))
            if match:
                out[k] = v

        return out
