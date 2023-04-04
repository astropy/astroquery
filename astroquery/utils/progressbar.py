# Licensed under a 3-clause BSD style license - see LICENSE.rst
import gzip
import sys
from io import StringIO
from urllib.request import build_opener
from astropy.io import fits


__all__ = ['chunk_report', 'chunk_read']


def chunk_report(bytes_so_far, chunk_size, total_size):
    if total_size > 0:
        percent = float(bytes_so_far) / total_size
        percent = round(percent * 100, 2)
        sys.stdout.write("Downloaded %12.2g of %12.2g Mb (%6.2f%%)\r" %
                         (bytes_so_far / 1024. ** 2, total_size / 1024. ** 2,
                          percent))
    else:
        sys.stdout.write("Downloaded %10.2g Mb\r" %
                         (bytes_so_far / 1024. ** 2))


def chunk_read(response, *, chunk_size=1024, report_hook=None):
    content_length = response.info().get('Content-Length')
    if content_length is None:
        total_size = 0
    else:
        total_size = content_length.strip()
        total_size = int(total_size)

    bytes_so_far = 0

    result_string = b""

    # sys.stdout.write("Beginning download.\n")

    while True:
        chunk = response.read(chunk_size)
        result_string += chunk
        bytes_so_far += len(chunk)

        if not chunk:
            if report_hook:
                sys.stdout.write('\n')
            break

        if report_hook:
            report_hook(bytes_so_far, chunk_size, total_size)

    return result_string


def retrieve(url, outfile, *, opener=None, overwrite=False):
    """
    "retrieve" (i.e., download to file) a URL.
    """

    if opener is None:
        opener = build_opener()

    page = opener.open(url)

    results = chunk_read(page, report_hook=chunk_report)

    S = StringIO(results)
    try:
        fitsfile = fits.open(S, ignore_missing_end=True)
    except OSError:
        S.seek(0)
        G = gzip.GzipFile(fileobj=S)
        fitsfile = fits.open(G, ignore_missing_end=True)

    fitsfile.writeto(outfile, clobber=overwrite)
