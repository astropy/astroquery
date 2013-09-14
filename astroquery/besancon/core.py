# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import print_function
import socket
import time
import copy
import sys
import re
import os
import astropy.utils.data as aud
from astropy.io import ascii
from . import BESANCON_DOWNLOAD_URL, BESANCON_MODEL_FORM, BESANCON_PING_DELAY, BESANCON_TIMEOUT
import urllib2  # only needed for urllib2.URLError

from ..query import BaseQuery
from ..utils.class_or_instance import class_or_instance
from ..utils import commons
from ..utils import prepend_docstr_noreturns
from ..utils import async_to_sync

__all__ = ['Besancon']

keyword_defaults = {
    'rinf':0.000000,
    'rsup':50.000000,
    'dist_step_mode':0,
    'dlr': 0.000,
    'kleg':1,
    'longit': 10.62,
    'latit':-0.38,
    'soli':0.0003,  # degrees.  0.00027777 = 1 arcsec
    'kleh':1,
    'eq1': 2000.0,
    'al0': 200.00,
    'alm': 200.00,
    'dl': 1.00,
    'ab0': 59.00,
    'abm': 59.00,
    'db': 1.00,
    'adif': 0.700,
    'ev':[""]*24,
    'di':[""]*24,
    'oo':[-7]+[-99]*12,
    'ff':[15]+[99]*12,
    'spectyp_min':1,
    'subspectyp_min': 0,
    'spectyp_max':9,
    'subspectyp_max': 5,
    'lumi':range(1,8),
    'sous_pop':range(1,11),
    'iband':8,
    'band0':[8]*9,
    'bandf':[25]*9,
    'colind':["J-H","H-K","J-K","V-K",],
    'nic': 4,
    'klea':1,
    'sc':[[0,0,0]]*9,
    'klee':0,
    'throughform':'ok',
    'kleb':3,  # 3 = Catalogue Simulation, 1 = tables and differential counts
    'klec':1,  # 1 = ubv, 15= cfhtls (photometric system)
    'cinem':0,  # 0: no kinematics, 1: kinematics
    'outmod':"",
}
keyword_defaults['ff[15]'] = 500
keyword_defaults['oo[15]'] = -500

colors_limits = {"J-H":(-99,99),"H-K":(-99,99),"J-K":(-99,99),"V-K":(-99,99)}
mag_limits = {'U':(-99,99), 'B':(-99,99), 'V':(-5,20), 'R':(-99,99),
              'I':(-99,99), 'J':(-99,99), 'H':(-99,99), 'K':(-99,99), 'L':(-99,99)}
mag_order = "U","B","V","R","I","J","H","K","L"


@async_to_sync
class Besancon(BaseQuery):

    # Since these are configuration options, they should probably be used directly
    # rather than re-stored as local variables.  Then again, we need to refactor
    # this whole project to be class-based, so they should be set for class
    # instances.
    url_download = BESANCON_DOWNLOAD_URL()
    QUERY_URL = BESANCON_MODEL_FORM()
    ping_delay = BESANCON_PING_DELAY()
    TIMEOUT = BESANCON_TIMEOUT()
    # sample file name:  1340900648.230224.resu
    result_re = re.compile("[0-9]{10}\.[0-9]{6}\.resu")

    def __init__(self, email=None):
        self.email = email

    @class_or_instance
    def get_besancon_model_file(self, filename, verbose=True, timeout=5.0):
        """
        Download a Besancon model from the website

        Parameters
        ----------
        filename : string
            The besancon filename, with format ##########.######.resu
        verbose : bool
            Print details about the download process
        timeout : float
            Amount of time to wait after pinging the server to see if a file is
            present.  Default 5s, which is probably reasonable.
        """

        url = os.path.join(self.url_download,filename)

        elapsed_time = 0
        t0 = time.time()

        if verbose:
            sys.stdout.write("Awaiting Besancon file...\n")
        while True:
            if verbose:
                sys.stdout.write(u"\r")
                sys.stdout.flush()
            try:
                # U = requests.get(url,timeout=timeout,stream=True)
                # TODO: add timeout= keyword to get_readable_fileobj (when PR https://github.com/astropy/astropy/pull/1258 is merged)
                with aud.get_readable_fileobj(url, cache=True) as f:
                    results = f.read()
                break
            except urllib2.URLError:
                if verbose:
                    sys.stdout.write(u"Waiting %0.1fs for model to finish (elapsed wait time %0.1fs, total wait time %0.1f)\r" % (self.ping_delay,elapsed_time,time.time()-t0))
                    sys.stdout.flush()
                time.sleep(self.ping_delay)
                elapsed_time += self.ping_delay
                continue
            except socket.timeout:
                if verbose:
                    sys.stdout.write(u"Waiting %0.1fs for model to finish (elapsed wait time %0.1fs, total wait time %0.1f)\r" % (self.ping_delay,elapsed_time,time.time()-t0))
                    sys.stdout.flush()
                time.sleep(self.ping_delay)
                elapsed_time += self.ping_delay
                continue

        return parse_besancon_model_string(results)

    @class_or_instance
    def _parse_result(self, response, verbose=False, retrieve_file=True):
        """
        retrieve_file : bool
            If True, will try to retrieve the file every 30s until it shows up.
            Otherwise, just returns the filename (the job is still executed on
            the remote server, though)
        """

        if verbose:
            print("Loading request from Besancon server ...")

        # keep the text stored for possible later use
        with aud.get_readable_fileobj(response.raw) as f:
            text = f.read()
        try:
            filename = self.result_re.search(text).group()
        except AttributeError:  # if there are no matches
            errors = parse_errors(text)
            raise ValueError("Errors: "+"\n".join(errors))

        if verbose:
            print("File is %s and can be aquired from %s" % (filename, self.url_download+'/'+filename))

        if retrieve_file:
            return self.get_besancon_model_file(filename)
        else:
            return filename

    @class_or_instance
    def _parse_args(self, glon, glat, email=None, smallfield=True, extinction=0.7,
                    area=0.0001, verbose=True, clouds=None,
                    absmag_limits=(-7,15), mag_limits=copy.copy(mag_limits),
                    colors_limits=copy.copy(colors_limits),
                    **kwargs):
        """
        Perform a query on the Besancon model of the galaxy
        http://model.obs-besancon.fr/

        Parameters
        ----------
        email : string
            A valid e-mail address to send the report of completion to
        glon : float
        glat : float
            Galactic latitude and longitude at the center
        smallfield : bool
            Small field (True) or Large Field (False)
            LARGE FIELD NOT SUPPORTED YET
        extinction : float
            Extinction per kpc in A_V
        area : float
            Area in square degrees
        absmag_limits : (float,float)
            Absolute magnitude lower,upper limits
        colors_limits : dict of (float,float)
            Should contain 4 elements listing color differences in the valid bands, e.g.:
                {"J-H":(99,-99),"H-K":(99,-99),"J-K":(99,-99),"V-K":(99,-99)}
        mag_limits = dict of (float,float)
            Lower and Upper magnitude difference limits for each magnitude band
            U B V R I J H K L
        clouds : list of 2-tuples
            Up to 25 line-of-sight clouds can be specified in pairs of (A_V,
            distance in pc)
        verbose : bool
            Print out extra error messages?
        kwargs : dict
            Can override any argument in the request if you know the name of the
            POST keyword.

        Returns
        -------
        Either the filename or the table depending on whether 'retrieve file' is
        specified
        """
        if email is None and hasattr(self,'email'):
            email = self.email
        if email is None or not isinstance(email,str) or not commons.validate_email(email):
            raise ValueError("Must specify a valid e-mail address.")

        # create a new keyword dict based on inputs + defaults
        kwd = copy.copy(keyword_defaults)
        for key,val in kwargs.iteritems():
            if key in keyword_defaults:
                kwd[key] = val
            elif verbose and not key in ('retrieve_file',):
                print("Skipped invalid key %s" % key)

        kwd['kleg'] = 1 if smallfield else 2
        if not smallfield:
            raise NotImplementedError

        kwd['longit'] = glon
        kwd['latit'] = glat

        kwd['adif'] = extinction
        kwd['soli'] = area
        kwd['oo'][0] = absmag_limits[0]
        kwd['ff'][0] = absmag_limits[1]

        for ii,(key,val) in enumerate(colors_limits.items()):
            if key[0] in mag_order and key[1] == '-' and key[2] in mag_order:
                kwd['colind'][ii] = key
                kwd['oo'][ii+9] = val[0]
                kwd['ff'][ii+9] = val[1]
            else:
                raise ValueError('Invalid color %s' % key)

        for (key,val) in mag_limits.iteritems():
            if key in mag_order:
                kwd['band0'][mag_order.index(key)] = val[0]
                kwd['bandf'][mag_order.index(key)] = val[1]
            else:
                raise ValueError('Invalid band %s' % key)

        if clouds is not None:
            for ii,(AV,di) in enumerate(clouds):
                kwd[AV][ii] = AV
                kwd[di][ii] = di

        # parse the default dictionary
        # request_data = parse_besancon_dict(keyword_defaults)
        request_data = kwd.copy()

        # convert all array elements to arrays
        for dummy in xrange(2):  # deal with nested lists
            for k,v in request_data.items():
                if isinstance(v,list) or (isinstance(v,tuple) and len(v) > 1):
                    if k in request_data:
                        del request_data[k]
                    for ii,x in enumerate(v):
                        request_data['%s[%i]' % (k,ii)] = x

        # an e-mail address is required
        request_data['email'] = email

        return request_data

    @class_or_instance
    @prepend_docstr_noreturns("\n"+_parse_args.__doc__+_parse_result.__doc__)
    def query_async(self, *args, **kwargs):
        """
        Returns
        -------
        response : `requests.Response` object
            The response of the HTTP request.
        """
        data_payload = self._parse_args(*args, **kwargs)
        if kwargs.get('get_query_payload'):
            return data_payload

        response = commons.send_request(
            self.QUERY_URL,
            data_payload,
            self.TIMEOUT,
            stream=True)
        return response


def parse_besancon_dict(bd):
    """
    Turn a dict like default_keys into a list of tuples (must be a list of
    tuples because there are some repeated entries, which dictionaries do not
    support)

    .. todo::
        In the future, a better way to do this is to make each dict entry a list;
        requests knows how to deal with this properly
    """

    http_dict = []
    for key,val in bd.iteritems():
        if isinstance(val, list):
            if "[]" in key:
                for listval in val:
                    http_dict.append((key,listval))
            else:
                for ii,listval in enumerate(val):
                    if isinstance(listval, list):
                        for jj,lv in enumerate(listval):
                            http_dict.append((key+"[%i][%i]" % (ii,jj),lv))
                    else:
                        http_dict.append((key+"[%i]" % (ii), listval))
        else:
            http_dict.append((key, val))

    return http_dict


def parse_errors(text):
    """
    Attempt to extract the errors from a Besancon web page with error messages in it
    """
    try:
        errors = re.compile(r"""<div\ class="?errorpar"?>\s*
                        <ol>\s*
                        (<li>([a-zA-Z0-9):( \s_-]*)</li>\s*)*\s*
                        </ol>\s*
                        </div>""", re.X)
        text = errors.search(text).group()
    except AttributeError:
        raise ValueError("Regular expression matching to error message failed.")
    text_items = re.split("<li>|</li>|\n",errors.search(text).group())
    text_items = [t for t in text_items if t != ""]
    error_list = text_items[2:-2]
    return error_list


def parse_besancon_model_string(bms,):
    """
    Given an entire Besancon model result in *string* form, parse it into an
    astropy table
    """

    header_start = "Dist    Mv  CL".split()

    # locate index of data start
    lines = bms.split('\n')
    nblanks = 0
    for ii,line in enumerate(lines):
        if line.strip() == '':
            nblanks += 1
        if all([h in line for h in header_start]):
            break

    names = line.split()
    ncols = len(names)
    data_start = ii
    first_data_line = lines[data_start]
    # ascii.read ignores blank lines
    data_start -= nblanks

    # locate index of data end
    nblanks = 0
    for ii,line in enumerate(lines[::-1]):
        if "TOTAL NUMBER OF STARS :" in line:
            nstars = int(line.split()[-1])
        if line.strip() == '':
            nblanks += 1
        if all([h in line for h in header_start]):
            break
    # most likely = -7
    data_end = -(ii-nblanks+1)

    # note: old col_starts/col_ends were:
    # (0,7,13,16,21,27,33,36,41,49,56,62,69,76,82,92,102,109)
    # (6,12,15,20,26,32,35,39,48,55,61,68,75,81,91,101,108,115)
    col_ends = [first_data_line.find(x)+len(x) for x in first_data_line.split()]
    col_starts = [0] + [c-1 for c in col_ends[:-1]]

    if len(col_starts) != ncols or len(col_ends) != ncols:
        raise ValueError("Table parsing error: mismatch between # of columns & header")

    besancon_table = ascii.read(bms, Reader=ascii.FixedWidthNoHeader,
                                header_start=None,
                                data_start=data_start,
                                names=names,
                                col_starts=col_starts,
                                col_ends=col_ends,
                                data_end=data_end)

    if len(besancon_table) != nstars:
        raise ValueError("Besancon table did not match reported size")

    for cn in besancon_table.columns:
        if besancon_table[cn].dtype.kind in ('s','S'):
            print("WARNING: The Besancon table did not parse properly.  Some columns are likely to have invalid values and others incorrect values.  Please report this error.")
            break

    return besancon_table
