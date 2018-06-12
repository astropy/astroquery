# Licensed under a 3-clause BSD style license - see LICENSE.rst
import textwrap


def append_docstr(doc):
    """ Decorator to append to the function's docstr """
    def dec(fn):
        fn.__doc__ += doc
        return fn
    return dec


def prepend_docstr_nosections(doc, sections=['Returns', ]):
    """
    Decorator to prepend to the function's docstr after stripping out the
    list of sections provided (by default "Returns" only).
    """
    def dec(fn):
        fn.__doc__ = ("\n".join(remove_sections(doc, sections)) +
                      textwrap.dedent(fn.__doc__))
        return fn
    return dec


def remove_sections(doc, sections):
    """
    Given a numpy-formatted docstring, remove the section blocks provided in
    ``sections`` and dedent the whole thing.

    Returns
    -------
    List of lines
    """

    lines = textwrap.dedent(doc).split('\n')
    outlines = []
    rblock = False
    for line in lines:
        lstrip = line.rstrip()
        if lstrip in sections:
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
