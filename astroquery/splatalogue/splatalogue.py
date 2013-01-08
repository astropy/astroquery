"""
Splatalogue Catalog Query Tool
-----------------------------------

REQUIRES mechanize

:Author: Magnus Vilehlm Persson (magnusp@vilhelm.nu)
"""

#~ import cookielib
#~ import urllib2
#~ import urllib
#~ import htmllib
#~ import formatter
#~ import gzip
#~ import os
#~ import astropy.io.fits as pyfits
#~ from math import cos, radians
#~ import multiprocessing as mp
#~ import time
#~ import StringIO
#~ from astroquery.utils import progressbar


SPLAT_FORM_URL = "http://www.cv.nrao.edu/php/splat/b.php"

__all__ = ['search_splatalogue']

try:
    import mechanize
except (ImportError):
    print "You need the \'mechanize\' module"

# since it is suppose to be part of astropy
# no need to check if it is installed
from astropy.table import Table

from scipy import array, where, arange



def search_splatalogue(
            freq = [203.4, 203.5],
            fwidth = None,
            funit = 'GHz',
            linelist = ['lovas', 'slaim', 'jpl', 'cdms', 'toyama', 'osu', 'recomb', 'lisa', 'rfi'],
            efrom = None,
            eto = None,
            etype = None,    # 'el_cm1', 'eu_cm1', 'el_k', 'eu_k'
            transition = None,
            lill = None,    # line intensity lower limits, 'cdms_jpl', 'sijmu2', 'aij'
             **settings):
    """
    
    Splatalogue.net search
    
    Function to search the Splatalogue.net compilation
    (http://www.splatalogue.net / http://www.cv.nrao.edu/php/splat/)
    
    
    Parameters
    ----------
    
    freq : Frequencies to search between. Give a single frequency if 
            'fwidth' is given.
    
    fwidth : Give only one frequency in 'freq' and a width in frequency
             here.
    
    funit : Frequency unit, 'GHz' or 'MHz'
    
    linelist : list of the molecular line catalogs to use
        available 
            'lovas'     - The LOVAS catalog http://
            'slaim'     - The SLAIM catalog http://
            'jpl'       - The JPL catalog http://
            'cdms'      - The CDMS catalog http://
            'toyama'    - The Toyama catalog http://
            'osu'       - The OSU catalog http://
            'recomb'    - The Recomd catalog http://
            'lisa'      - The LISA catalog http://
            'rfi'       - The RFI catalog http://
            For example, give linelist = ['cdms', 'jpl'] to use only 
            the CDMS and JPL catalogs.
    
    efrom : Limit of the lower energy level

    eto : Upper limit of the upper energy level

    eunit : Unit of the given energy levels 
            Available : 'el_cm1', 'eu_cm1', 'el_k', 'eu_k'

    transition : Transition numbers of the line as a string, 
                 e.g. '1-0'

    lill : Line intensity lower limits. A list of first the 
           limit and then the format [value, 'type']
           Available formats : 'cdms_jpl', 'sijmu2', 'aij'
           Example: lill = [-5, 'cdms_jpl'] for 
           CDMS/JPL Intensity of 10^(-5)
    
    
    Parameters
    ----------
    
    
    Returns
    -------
    
    
    Notes
    -----
    
    
    """

    form = _get_form()
    
    
    #### FREQUENCY
    # Two casees:
    #   1. A list with length two
    #   2. A integer/float
    if type(freq) == str:
        # Format error, TypeError?
        #~ raise(TypeError, 'Wrong format for frequency. Need list or float')
        raise(Exception, 'Wrong format for frequency. Need list or float')
    # First guess : a list of floats with length two
    try:
        form['from'] = str(freq[0])
        form['to'] = str(freq[1])
    except (IndexError, TypeError):
        # If not a list, should be a float, and fwidth given
        try:
            freq = float(freq)
        except (ValueError)
            raise (Exception, 'Wrong format for frequency. Need list or float')
        if dfreq not in [0, 0.0, None]:
            # with freq and fwidth given, we can calculate start and end
            f1, f2 = freq + array([-1,1]) * fwidth / 2.
            form['from'] = str(f1)
            form['to'] = str(f2)
        else:
            # the fwidth parameter is missing
            raise (Exception, 'The fwidth parameter is missing. '
            'Frequency parameter(s) malformed')
    #### FREQUENCY UNIT
    #
    if funit not in [0, None]:
        if funit.lower() in ['ghz', 'mhz']:
            form['frequency_units'] = [funit]
        else:
            print 'Allowed frequency units : \'GHz\' or \'MHz\''
    elif not funit in [0, None]:
        funit = 'GHz'
        form['frequency_units'] = ['GHz']
        
        
    ####################################################################
    ####################################################################
    ####################################################################
    # OLD, copy from below and change above to better code
    if arg.has_key('freq'):
        if type(arg['freq']) == type([1,2]):
            if len(arg['freq']) == 1:
                raise ParError(arg['freq'])
            f1, f2 = arg['freq']
            form['from'] = str(f1)
            form['to'] = str(f2)
        elif type(arg['freq']) == type(1) or type(arg['freq']) == type(1.):
            if type(arg['freq']) == type(1):
                arg['freq'] = float(arg['freq'])
            if not arg.has_key('dfreq'):
                print 'Please either give a frequency interval (freq=[f1,f2])\n\
                OR a center frequency and a bandwidth (freq=f, dfreq=df)'
                raise ParError('freq='+str(arg['freq'])+' and dfreq=None')
            elif arg.has_key('dfreq'):
                f1, f2 = arg['freq']+array([-1,1])*arg['dfreq']/2.
            else:
                raise ParError(arg['dfreq'])
            form['from'] = str(f1)
            form['to'] = str(f2)
    elif not arg.has_key('freq') and arg.has_key('dfreq'):
        print 'Only delta-frequency (dfreq) given, no frequency to look for'
        raise ParError('freq=None and dfreq='+str(arg['dfreq']))
    elif not arg.has_key('freq') and not arg.has_key('dfreq') and len(arg.keys()) != 0:
        # no frequency given, but other parameters
        #tmp = str(raw_input('No frequency limits given, continue? Press Enter to continue, Ctrl+C to abort.'))
        f1 = ''
        f2 = ''
    else:
        # if no frequency is given, just run example
        # this is not visible when running from outside python
        # check "if __main__ ..." part
        print stylify('Example run... setting f1,f2 = 203.406, 203.409 GHz',fg='m')
        form['from'] = '203.406'
        form['to'] = '203.409'
    #
    #### FREQUENCY UNIT
    #
    if arg.has_key('funit'):
        if arg['funit'].lower() in ['ghz', 'mhz']:
            form['frequency_units'] = [arg['funit']]
        else:
            print 'Allowed frequency units : \'GHz\' or \'MHz\''
    elif not arg.has_key('funit'):
        arg['funit'] = 'GHz'
        form['frequency_units'] = ['GHz']
    #
    #### MOLECULAR SPECIES
    #
    #Get species molecular number, ordered by mass
    # TODO : perhaps be able to search in this one
    #        either by mass or by species, text of chem formula
    # TODO : after getting it, should sort the list of dictionaries
    #        clean it up a bit
    # get the avaliable species from the form
    #~ sel_species = [i.attrs for i in form.find_control('sid[]').items]
    #
    #### LINE LIST
    #
    # define a reference list of names
    mylinelist = ['lovas', 'slaim', 'jpl', 'cdms', 'toyama', 'osu', \
    'recomb', 'lisa', 'rfi']
    # list of strings with the format that the search form wants
    formcontrol_linelist = ["displayLovas", "displaySLAIM", \
    "displayJPL", "displayCDMS", "displayToyaMA", "displayOSU", \
    "displayRecomb", "displayLisa", "displayRFI"]
    if arg.has_key('linelist'):
        if type(arg['linelist'])==type('string'):
            # if linelist is given as linelist='all'
            if arg['linelist'].lower() == 'all':
                # if we want to set all, just copy mylinelist
                arg['linelist'] = mylinelist
            else:
                print 'Linelist input not understood'
                raise ParError(arg['linelist'])
        elif type(arg['linelist'])==type(['list']):
            # get all values to lower case, to accept capitals
            arg['linelist'] = [x.lower() for x in arg['linelist']]
        else:
            print 'Linelist input not understood'
            raise ParError(arg['linelist'])
    else:
        # if none given, search with all
        arg['linelist'] = mylinelist

    # now set the linelist search form
    # check for every linelist, if it exists in the input linelist
    for i,j in zip(mylinelist, formcontrol_linelist):
        if i in arg['linelist']:
            form.find_control(j).get().selected = True
        else:
            form.find_control(j).get().selected = False
    # ['Lovas', 'SLAIM', 'JPL', 'CDMS', 'ToyaMA', 'OSU', \
    #'Recomb', 'Lisa', 'RFI']
    # Figure out prettier printing here...
    #    web-adresses?
    #
    ### Energy Range
    #
    # form['energy_range_from/to'] is a text field in the form
    # while it is called e_from/to in the function
    #
    if arg.has_key('e_from') or arg.has_key('e_to'):
        e_type_ref = ['el_cm1', 'eu_cm1', 'el_k', 'eu_k']
        # check that unit is given, and correct
        # or set default (eu_k)

        if arg.has_key('e_from'):
            form['energy_range_from'] = str(arg['e_from'])
        if arg.has_key('e_to'):
            form['energy_range_to'] = str(arg['e_to'])
        if arg.has_key('e_from') or arg.has_key('e_to'):
            if arg.has_key('e_type'):
                if arg['e_type'].lower() in e_type_ref:
                    pass
                else:
                    print 'Energy range type keyword \'e_type\' malformed.'
                    raise ParError(arg['e_type'])
                e_type_default = 0
            else:
                e_type_default = 1
                arg['e_type'] = 'eu_k'
            # now set the radio button to the correct value
            form.find_control('energy_range_type').toggle(arg['e_type'].lower())
        if not arg.has_key('e_from') and not arg.has_key('e_to') and arg.has_key('e_type'):
            print 'You gave the Enery range type keyword, but no energy range...'
            raise ParError(arg['e_type'])
    #
    ### Specify Transition
    #
    if arg.has_key('transition'):
        form['tran'] = str(arg['transition'])
    #
    ### Line Intensity Lower Limits
    if arg.has_key('lill'):
        if arg['lill'][1].lower() == 'cdms_jpl':
            form.find_control('lill_cdms_jpl').disabled = False
            form['lill_cdms_jpl'] = str(arg['lill'][0])
        elif arg['lill'][1].lower() == 'sijmu2':
            form.find_control('lill_sijmu2').disabled = False
            form['lill_sijmu2'] = str(arg['lill'][0])
        elif arg['lill'][1].lower() == 'aij':
            form.find_control('lill_aij').disabled = False
            form['lill_aij'] = str(arg['lill'][0])
    #
    ### FREQUENCY ERROR LIMIT
    #

    #### Line Strength Display
    form.find_control("ls1").get().selected = True
    form.find_control("ls2").get().selected = True
    form.find_control("ls3").get().selected = True
    form.find_control("ls4").get().selected = True
    form.find_control("ls5").get().selected = True
    #### Energy Levels
    form.find_control("el1").get().selected = True
    form.find_control("el2").get().selected = True
    form.find_control("el3").get().selected = True
    form.find_control("el4").get().selected = True
    #### Miscellaneous
    form.find_control("show_unres_qn").get().selected = True
    form.find_control("show_upper_degeneracy").get().selected = True
    form.find_control("show_molecule_tag").get().selected = True
    form.find_control("show_qn_code").get().selected = True
    

    return None


def _get_form():
    # GET SERVER RESPONSE
    try:
        response = mechanize.urlopen(SPLAT_FORM_URL)
    except mechanize.URLError, e:
        raise Exception('No reponse from server : {0}'.format(splatalogue_url))
    
    # PARSE SERVER RESPONSE
    forms = mechanize.ParseResponse(response, backwards_compat = False)
    response.close()
    
    # GET FORM
    form = forms[0]
    return form


def _parse_input_form(form):
    # PARSE INPUT AND FILL IN FORM

    return None




# Get/Parse form
# Fill in form
# Submit form
# Get/Parse results
# Return results in a given structure (astrpy.table.Table?)






"""
from astro import table as _table

_table.Table()

Parameters
----------
data : numpy ndarray, dict, list, or Table, optional
    Data to initialize table.
names : list, optional
    Specify column names
dtypes : list, optional
    Specify column data types
meta : dict, optional
    Metadata associated with the table
copy : boolean, optional
    Copy the input data (default=True).
Constructor information:
 Definition:table.Table(self, data=None, names=None, dtypes=None, meta=None, copy=True)

for example:

t = table.Table(data=array([['line1',10],['line2',40]]), names=['name', 'value'], dtypes=['str', 'float'])


"""
