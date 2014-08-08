# Licensed under a 3-clause BSD style license - see LICENSE.rst
from astropy.io.ascii import core
from astropy.io.ascii import fixedwidth

__all__ = ['BesanconFixed',
           'BesanconFixedWidthHeader',
           'BesanconFixedWidthData',
           ]


class BesanconFixed(fixedwidth.FixedWidth):

    """
    Read data from a Besancon galactic model table file.

    Assumes a fixed-length header;
    it is possible that different parameters in the model
    will result in different length headers
    """

    def __init__(self, col_starts=None, col_ends=None, delimiter_pad=' ', bookend=True,
                 header_line=80, footer_line=-6):
        core.BaseReader.__init__(self)

        self.header = BesanconFixedWidthHeader()
        self.data = BesanconFixedWidthData()

        self.data.header = self.header
        self.header.data = self.data

        # These should NOT be necessary - BesaconFixedWidthHeader.get_cols should find these
        # however, they're not set early enough, apparently
        self.header.header_line = header_line
        self.header.footer_line = footer_line

        self.header.splitter.delimiter = ' '
        self.header.splitter.delimiter = ' '
        self.header.start_line = 0
        self.header.comment = r'\s*#'
        self.header.write_comment = '# '
        self.header.col_starts = col_starts
        self.header.col_ends = col_ends


class BesanconFixedWidthHeader(fixedwidth.FixedWidthHeader):

    def get_cols(self, lines):
        # super(BesanconFixedWidthHeader,self).get_cols(lines)

        header_inds = [ii for ii, L in enumerate(lines) if "  Dist    Mv  CL" in L]
        self.header_line = header_inds[0]
        self.footer_line = header_inds[1]
        self.data.start_line = header_inds[0] + 1
        self.data.end_line = header_inds[1] - 1
        self.names = lines[self.header_line].split()

        self.data.process_lines(lines)
        vals1, starts1, ends1 = self.get_fixedwidth_params(lines[self.header_line + 1])
        vals2, starts2, ends2 = self.get_fixedwidth_params(lines[self.footer_line - 1])

        starts = [min(s1, s2) for s1, s2 in zip(starts1, starts2)]
        ends = [max(e1, e2) for e1, e2 in zip(ends1, ends2)]

        self._set_cols_from_names()
        self.n_data_cols = len(self.cols)

        # Set column start and end positions.  Also re-index the cols because
        # the FixedWidthSplitter does NOT return the ignored cols (as is the
        # case for typical delimiter-based splitters)
        for i, col in enumerate(self.cols):
            col.start = starts[col.index]
            col.end = ends[col.index]
            col.index = i

    def process_lines(self, lines):
        """Strip out comment lines from list of ``lines``.

        Unlike the normal process_lines, does NOT exclude blank lines.

        Parameters
        ----------
        lines : TODO
            All lines in table

        Returns
        -------
        list of lines
        """
        return lines[self.header_line + 1:self.footer_line]


class BesanconFixedWidthData(fixedwidth.FixedWidthData):

    def process_lines(self, lines):
        """Strip out comment lines from list of ``lines``.

        Unlike the normal process_lines, does NOT exclude blank lines.

        Parameters
        ----------
        lines : TODO
            All lines in table

        Returns
        -------
        list of lines
        """
        return lines[self.header.header_line + 1:self.header.footer_line]
