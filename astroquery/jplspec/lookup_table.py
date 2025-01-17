# Licensed under a 3-clause BSD style license - see LICENSE.rst
import re


class Lookuptable(dict):

    def find(self, st, flags):
        """
        Search dictionary keys for a regex match to string s

        Parameters
        ----------
        st : str
            String to compile as a regular expression
            Can be entered non-specific for broader results
            ('H2O' yields 'H2O' but will also yield 'HCCCH2OD')
            or as the specific desired regular expression for
            catered results, for example: ('H20$' yields only 'H2O')

        flags : int
            Regular expression flags.

        Returns
        -------
        The dictionary containing only values whose keys match the regex

        """

        if st in self:
            return {st: self[st]}

        R = re.compile(st, flags)

        out = {}

        for key, val in self.items():
            match = R.search(str(key))
            if match:
                out[key] = val

        return out
