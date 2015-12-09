# Licensed under a 3-clause BSD style license - see LICENSE.rst
import textwrap


def append_docstr(doc):
    """ Decorator to append to the function's docstr """
    def dec(fn):
        fn.__doc__ += doc
        return fn
    return dec


def prepend_docstr_noreturns(doc):
    """
    Decorator to prepend to the function's docstr after stripping out the
    "Returns".
    """
    def dec(fn):
        fn.__doc__ = ("\n".join(remove_returns(doc)) +
                      textwrap.dedent(fn.__doc__))
        return fn
    return dec


def remove_returns(doc):
    """
    Given a numpy-formatted docstring, remove the "Returns" block
    and dedent the whole thing.

    Returns
    -------
    List of lines
    """

    lines = textwrap.dedent(doc).split('\n')
    outlines = []
    rblock = False
    for line in lines:
        lstrip = line.rstrip()
        if lstrip == "Returns":
            rblock = True
            continue
        elif rblock:
            if lstrip == '':
                rblock = False
                continue
            else:
                continue
        else:
            outlines.append(lstrip)

    return outlines
