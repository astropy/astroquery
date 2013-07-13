# Licensed under a 3-clause BSD style license - see LICENSE.rst
import socket
import time
import copy
import os
import sys
import re
import astropy.utils.data as aud
import astropy.io.ascii as asciireader
from . import BESANCON_DOWNLOAD_URL, BESANCON_MODEL_FORM, BESANCON_PING_DELAY
import requests

__all__ = ['get_besancon_model_file','request_besancon']

keyword_defaults = {
    'rinf':0.000000,
    'rsup':50.000000,
    'dist_step_mode':0,
    'dlr':  0.000,
    'kleg':1,
    'longit': 10.62,
    'latit':-0.38,
    'soli':0.0003, # degrees.  0.00027777 = 1 arcmin
    'kleh':1,
    'eq1': 2000.0,
    'al0': 200.00,
    'alm': 200.00,
    'dl':  1.00,
    'ab0':  59.00,
    'abm':  59.00,
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
    'lumi[]':range(1,8),
    'sous_pop[]':range(1,11),
    'iband':8,
    'band0':[8]*9,
    'bandf':[25]*9,
    'colind':["J-H","H-K","J-K","V-K",],
    'nic':  4,
    'klea':1,
    'sc':[[0,0,0]]*9,
    'klee':0,
    'throughform':'ok',
    'kleb':3,
    'klec':1,
    'cinem':0,
    'outmod':"",
}

# Since these are configuration options, they should probably be used directly
# rather than re-stored as local variables.  Then again, we need to refactor
# this whole project to be class-based, so they should be set for class
# instances.
url_download = BESANCON_DOWNLOAD_URL()
url_request = BESANCON_MODEL_FORM()
ping_delay = BESANCON_PING_DELAY()
# sample file:  1340900648.230224.resu
result_re = re.compile("[0-9]{10}\.[0-9]{6}\.resu")

def parse_besancon_dict(bd):
    """
    Turn a dict like default_keys into a list of tuples (must be a list of
    tuples because there are some repeated entries, which dictionaries do not
    support)
    """

    http_dict = []
    for key,val in bd.iteritems():
        if type(val) is list:
            if "[]" in key:
                for listval in val:
                    http_dict.append((key,listval))
            else:
                for ii,listval in enumerate(val):
                    if type(listval) is list:
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

    
colors_limits = {"J-H":(-99,99),"H-K":(-99,99),"J-K":(-99,99),"V-K":(-99,99)}
mag_limits = {'U':(-99,99), 'B':(-99,99), 'V':(-5,20), 'R':(-99,99),
              'I':(-99,99), 'J':(-99,99), 'H':(-99,99), 'K':(-99,99), 'L':(-99,99)}
mag_order = "U","B","V","R","I","J","H","K","L"

def request_besancon(email, glon, glat, smallfield=True, extinction=0.7,
                     area=0.0001, verbose=True, clouds=None,
                     absmag_limits=(-7,15), mag_limits=copy.copy(mag_limits),
                     colors_limits=copy.copy(colors_limits),
                     retrieve_file=True, **kwargs):
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
    retrieve_file : bool
        If True, will try to retrieve the file every 30s until it shows up.
        Otherwise, just returns the filename (the job is still executed on
        the remote server, though)
    kwargs : dict
        Can override any argument in the request if you know the name of the
        POST keyword.

    Returns
    -------
    Either the filename or the table depending on whether 'retrieve file' is
    specified

    """

    # create a new keyword dict based on inputs + defaults
    kwd = copy.copy(keyword_defaults)
    for key,val in kwargs.iteritems():
        if key in keyword_defaults:
            kwd[key] = val
        elif verbose:
            print "Skipped invalid key %s" % key

    kwd['kleg'] = 1 if smallfield else 2
    if not smallfield:
        raise NotImplementedError

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
    request_data = parse_besancon_dict(keyword_defaults)

    # an e-mail address is required
    request_data.append(('email',email))
    request_data = dict(request_data)

    # load the URL as text
    response = requests.post(url_request, data=request_data)

    if verbose:
        print "Loading request from Besancon server ..."

    # keep the text stored for possible later use
    with aud.get_readable_fileobj(response) as f:
        text = f.read()
    try:
        filename = result_re.search(text).group()
    except AttributeError: # if there are no matches
        errors = parse_errors(text)
        raise ValueError("Errors: "+"\n".join(errors))

    if verbose:
        print "File is %s and can be aquired from %s" % (filename, url_download+filename)

    if retrieve_file:
        return get_besancon_model_file(filename)
    else:
        return filename

def get_besancon_model_file(filename, verbose=True, save=True, savename=None, overwrite=True,
        timeout=5.0):
    """
    Download a Besancon model from the website

    Parameters
    ----------
    filename : string
        The besancon filename, with format ##########.######.resu
    verbose : bool
        Print details about the download process
    save : bool
        Save the table after acquiring it?
    savename : None or string
        If not specified, defaults to the .resu table name
    overwrite : bool
        Overwrite the file if it exists?  Defaults to True because the .resu
        tables should have unique names by default, so there's little risk of
        accidentally overwriting important information
    timeout : float
        Amount of time to wait after pinging the server to see if a file is
        present.  Default 5s, which is probably reasonable.
    """

    url = url_download+filename

    elapsed_time = 0
    t0 = time.time()

    sys.stdout.write("\n")
    while 1:
        sys.stdout.write(u"\r")
        try:
            U = requests.get(url,timeout=timeout)
            with aud.get_readable_fileobj(U, cache=True) as f:
                results = f.read()
            break
        except requests.ConnectionError:
            sys.stdout.write(u"Waiting %0.1fs for model to finish (elapsed wait time %is, total %i)\r" % (ping_delay,elapsed_time,time.time()-t0))
            time.sleep(ping_delay)
            elapsed_time += ping_delay
            continue
        except socket.timeout:
            sys.stdout.write(u"Waiting %0.1fs for model to finish (elapsed wait time %is, total %i)\r" % (ping_delay,elapsed_time,time.time()-t0))
            time.sleep(ping_delay)
            elapsed_time += ping_delay
            continue


    if save:
        if savename is None:
            savename = filename
        if not overwrite and os.path.exists(savename):
            raise IOError("File %s already exists." % savename)
        outf = open(savename,'w')
        print >>outf,results
        outf.close()

    return parse_besancon_model_string(results)

def parse_besancon_model_string(bms,):

    besancon_table = asciireader.read(bms, Reader=asciireader.FixedWidth,
                                      header_start=None, data_start=81,
                                      names=bms.split('\n')[80].split(),
                                      col_starts=(0,7,13,16,21,27,33,36,41,49,56,62,69,76,82,92,102,109),
                                      col_ends=(6,12,15,20,26,32,35,39,48,55,61,68,75,81,91,101,108,115),
                                      data_end=-7)

    for cn in besancon_table.columns:
        if besancon_table[cn].dtype.kind in ('s','S'):
            print "WARNING: The Besancon table did not parse properly.  Some columns are likely to have invalid values and others incorrect values.  Please report this error."
            break

    return besancon_table


