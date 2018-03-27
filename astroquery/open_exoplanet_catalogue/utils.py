# Licensed under a 3-clause BSD style license - see LICENSE.rst


class Number(object):
    """ Number class for values containing errors. Math operations use
    the value given. Checking for no 'value' must use "==". Numbers with
    upper or lower limits as assumed to have no value.

    Examples
    --------

    >>> num = Number(10, errorminus=0.5, errorplus=0.8)
    >>> str(num)
    '10.0 +0.8 -0.5'

    >>> num * 2
    20.0

    >>> num + 2
    12.0

    >>> num.errorminus
    0.5

    >>> num = Number(None, upperlimit=10)
    >>> str(num)
    '<10.0'

    >>> num == None
    True

    >>> num is None
    False
    """

    def __init__(self, value=None, upperlimit=None, lowerlimit=None,
                 errorplus=None, errorminus=None):
        """
        Parameters
        ----------
        value: float
            the value of this number. Numbers with upper or lower limits
            assume None as value.
        upperlimit: float
            if upper limit exists, there should be no value
        lowerlimit: float
            if lower limit exists, there should be no value
        errorplus: float
            unsigned value
        errorminus: float
            unsigned value

        Notes
        -----

        Number object acts as a typical float object, but can hold
        errorminus, errorplus, lowerlimit, upperlimit mathematical
        operations only use value attribute. Number == Number will compare
        the error values as well as value.

        Returns
        -------
        Number object.
        """
        if value is None:
            self.value = None
        else:
            try:
                self.value = float(value)
            except ValueError:
                self.value = value
        self.upperlimit = upperlimit
        self.lowerlimit = lowerlimit
        self.errorplus = errorplus
        self.errorminus = errorminus

    def __str__(self):
        """
        Example outputs
        ---------------
        >>> str(Number(2.0))
        '2.0'
        >>> str(Number(2.0, errorplus=1.0, errorminus=1.5))
        '2.0 +1.0 -1.5'
        >>> str(Number(2.0, errorplus=1.0, errorminus=1.0))
        '2.0 +/-1.0'
        >>> str(Number(lowerlimit=2.0))
        '>2.0'
        >>> str(Number(upperlimit=2.0))
        '<2.0'
        """

        tempstr = ""
        if self.value is not None:
            tempstr += str(self.value)
        if hasattr(self, "errorplus") and self.errorplus is not None and\
                hasattr(self, "errorminus") and self.errorminus is not None:
            if self.errorplus == self.errorminus:
                tempstr += " +/-" + str(self.errorplus)
            else:
                tempstr += (" +" + str(self.errorplus) + " -" +
                            str(self.errorminus))
        if hasattr(self, "upperlimit") and self.upperlimit is not None:
            tempstr += "<" + str(self.upperlimit)
        elif hasattr(self, "lowerlimit") and self.lowerlimit is not None:
            tempstr += ">" + str(self.lowerlimit)
        return tempstr

    def machine_readable(self, separator="\t", missingval="None"):
        """
        Creates a string intended for a machine to read (ex, gnuplot)
        prints as follows
        value(separator)errorplus(separator)errorminus(separator)upperlimit(separator)lowerlimit

        if the value does not exist, the missingval is added instead

        Parameters
        ----------
        separator: str
            string used to separate values while printing
        missingval: str
            string to use for NoneType values

        Returns
        -------
        str
        """

        temp = ""
        if hasattr(self, "value") and self.value is not None:
            temp += str(self.value) + separator
        else:
            temp += missingval + separator
        if hasattr(self, "errorplus") and self.errorplus is not None:
            temp += str(self.errorplus) + separator
        else:
            temp += missingval + separator
        if hasattr(self, "errorminus") and self.errorminus is not None:
            temp += str(self.errorminus) + separator
        else:
            temp += missingval + separator
        if hasattr(self, "upperlimit") and self.upperlimit is not None:
            temp += str(self.upperlimit) + separator
        else:
            temp += missingval + separator
        if hasattr(self, "lowerlimit") and self.lowerlimit is not None:
            temp += str(self.lowerlimit) + separator
        else:
            temp += missingval + separator
        return temp.strip(separator)

    def __setattr__(self, key, val):
        if val is not None:
            try:
                self.__dict__[key] = float(val)
            except ValueError:
                self.__dict__[key] = val
        else:
            self.__dict__[key] = val

    def __eq__(self, num):
        """
        Parameters
        ----------
        num: Number, float or int
            Number types check both the value and the uncertainties.

        Returns
        -------
        bool
        """
        if isinstance(num, Number):
            return self.value == num.value and\
                self.errorminus == num.errorminus and\
                self.errorplus == num.errorplus and\
                self.lowerlimit == num.lowerlimit and\
                self.upperlimit == num.upperlimit
        else:
            return self.value == num

    def __add__(self, num):
        return self.value + num

    def __sub__(self, num):
        return self.value - num

    def __lt__(self, num):
        return self.value < num

    def __le__(self, num):
        return self.value <= num

    def __ne__(self, num):
        """
        Parameters
        ----------
        num: Number, float or int
            Number types check both the value and the uncertainties.

        Returns
        -------
        bool
        """

        if isinstance(num, Number):
            return self.value != num.value and\
                self.errorminus != num.errorminus and\
                self.errorplus != num.errorplus
        else:
            return self.value != num

    def __gt__(self, num):
        return self.value > num

    def __ge__(self, num):
        return self.value >= num

    def __mul__(self, num):
        return self.value * num

    def __div__(self, num):
        return self.value / num

    def __floordiv__(self, num):
        return self.value // num

    def __mod__(self, num):
        return self.value % num

    def __divmod__(self, num):
        return divmod(self.value, num)

    def __pow__(self, num, *z):
        return pow(self.value, num, *z)

    def __float__(self):
        return float(self.value)

    def __cmp__(self, num):
        return cmp(self.value, num)

    def __and__(self, num):
        return self.value & num

    def __abs__(self):
        return abs(self.value)

    def __coerce__(self, num):
        return coerce(self.value, num)

    def __hash__(self):
        return hash(self.value)

    def __hex__(self):
        return hex(self.value)

    def __int__(self):
        return int(self.value)

    def __invert__(self):
        return ~self.value

    def __long__(self):
        return long(self.value)

    def __lshift__(self, num):
        return self.value << num

    def __neg__(self):
        return -self.value

    def __nonzero__(self):
        return self.value != 0

    def __oct__(self):
        return oct(self.value)

    def __or__(self, num):
        return self.value | num

    def __pos__(self):
        return +self.value

    def __radd__(self, num):
        return num + self.value

    def __rdiv__(self, num):
        return num / self.value

    def __rdivmod(self, num):
        return divmod(num, self.value)

    def __repr__(self):
        return str(self)

    def __rfloordiv__(self, num):
        return num // self.value

    def __rlshift__(self, num):
        return num << self.value

    def __rmod__(self, num):
        return num % self.value

    def __rmul__(self, num):
        return num * self.value

    def __ror__(self, num):
        return num | self.value

    def __rpow__(self, num, *z):
        return pow(num, self.value, *z)

    def __rrshift__(self, num):
        return num >> self.value

    def __rshift__(self, num):
        return self.value >> num

    def __rsub__(self, num):
        return num - self.value

    def __rtruediv__(self, num):
        return num / self.value

    def __rxor__(self, num):
        return num ^ self.value

    def __truediv__(self, num):
        return self.value / num

    def __xor__(self, num):
        return self.value ^ num

    def bit_length(self):
        return self.value.bit_length()

    def asymmetric(self):
        """
        Notes
        -----
        Returns true if the errorplus and errorminus are not equal

        Returns
        -------
        bool
        """

        return self.errorminus != self.errorplus
