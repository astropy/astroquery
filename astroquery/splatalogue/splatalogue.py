"""
Splatalogue Catalog Query Tool
-----------------------------------

REQUIRES mechanize (and astropy)

.. TODO::
    Replace mechanize with standard module

:Author: Magnus Vilehlm Persson (magnusp@vilhelm.nu)
"""


SPLAT_FORM_URL = "http://www.cv.nrao.edu/php/splat/b.php"

__all__ = ['search']

try:
    import mechanize
except ImportError:
    print "You need the \'mechanize\' module"

from astropy.table import Table

from numpy import array, arange


"""
TODO : fix consistent naming (resultform vs result_table)
TODO : improve the parsing, i.e., the astropy.table output
TODO : create pretty printing for on screen results?
TODO : improve searchable parameters e.g. molecule ID, 
       frequency error limit

"""

def search(
            freq = [203.4, 203.42],
            fwidth = None,
            funit = 'GHz',
            linelist = ['lovas', 'slaim', 'jpl', 'cdms', 'toyama', 'osu', 'recomb', 'lisa', 'rfi'],
            efrom = None,
            eto = None,
            eunit = None,    # 'el_cm1', 'eu_cm1', 'el_k', 'eu_k'
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
   
   Extra parameters:
   transition : search (just like on Splatalogue.net) for a specific 
                transition, e.g., "1-0"
   
    
    Returns
    -------
    A astropy.table table, with column names, units and description.
    
    
    Notes
    -----
    The naming of the columns in the results table, and the units is 
    not complete. The names should be optimized and the units (at 
    least some) should be taken from the input and/or results. 
    So beware.
    The column descriptions is not done either, so it is empty.
    
    It queries splatalogue.net over http (mechanize/urllib), so don't 
    write a script that queries their server too often.
    
    Example
    -------
    In : from astroquery import splatalogue
    In : results = splatalogue.search()
    
    and e.g.
    
    In : results['Freq-GHz'][results['Chemical Name'] == 'UNIDENTIFIED']
    Out : <Column name='Freq-GHz' units='GHz?' format=None description=None> array([ 203.4127])
    
    to get the frequency of the unidentified line(s)
    
    (It will search between 203.4 and 203.42 GHz by default, giving
    about 69 hits.)
    
    
    
    """
    # Get the form from the server
    form = _get_form()
    # Frequency
    form = _parse_frequency(form, freq, fwidth, funit)
    # Molecular species
    #Get species molecular number, ordered by mass
    # PLACEHOLDER for future implementation
    # get the avaliable species from the form
    #~ sel_species = [i.attrs for i in form.find_control('sid[]').items]
    form = _parse_molecular_species(form)
    # Line list
    form = _parse_linelist(form, linelist)
    # Energy range
    form = _parse_enrgy_range(form, efrom, eto, eunit)
    # Specify transition
    form = _parse_transition(form, settings)
    # Line intensity lower limit
    form = _parse_line_intensity(form, lill)
    # Frequency error limit
    form = _parse_frequency_error_limit(form)
    # Other settings
    form = _set_settings(form)
    # Press search and get the result
    data = _get_results(form)
    # Parse the data into a astropy.table
    results = _parse_result(data, output='astropy.table')
    
    # at the moment just returns the results astropy.table
    return results


def _get_form():
    # GET SERVER RESPONSE
    try:
        response = mechanize.urlopen(SPLAT_FORM_URL)
    except mechanize.URLError:
        raise Exception('No reponse from server : {0}'.format(SPLAT_FORM_URL))
    
    # PARSE SERVER RESPONSE
    forms = mechanize.ParseResponse(response, backwards_compat = False)
    response.close()
    
    # GET FORM
    form = forms[0]
    return form

def _parse_frequency(form, freq, fwidth, funit):
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
        except (ValueError):
            raise (Exception, 'Wrong format for frequency. Need list or float')
        if fwidth not in [0, 0.0, None]:
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
    return form

def _parse_molecular_species(form):
    return form
    
def _parse_linelist(form, linelist):
    #### LINE LIST
    # define a reference list of names
    mylinelist = ['lovas', 'slaim', 'jpl', 'cdms', 'toyama', 'osu', \
    'recomb', 'lisa', 'rfi']
    # list of strings with the format that the search form wants
    formcontrol_linelist = ["displayLovas", "displaySLAIM", \
    "displayJPL", "displayCDMS", "displayToyaMA", "displayOSU", \
    "displayRecomb", "displayLisa", "displayRFI"]
    if type(linelist) == type('string'):
        # if linelist is given as linelist='all'
        if linelist.lower() == 'all':
            # if we want to set all, just copy mylinelist
            linelist = mylinelist
        else:
            print 'Linelist input not understood'
            raise Exception('bad input : \'linelist\'')
    elif type(linelist) == type(['list']):
        # get all values to lower case, to accept capitals
        linelist = [x.lower() for x in linelist]
    else:
        raise Exception('something is wrong with the linelist input/parsing')

    # now set the linelist search form
    # check for every linelist, if it exists in the input linelist
    for i,j in zip(mylinelist, formcontrol_linelist):
        if i in linelist:
            form.find_control(j).get().selected = True
        else:
            form.find_control(j).get().selected = False

    return form

def _parse_enrgy_range(form, efrom, eto, eunit):
    ### Energy Range
    # form['energy_range_from/to'] is a text field in the form
    # while it is called e_from/to in the function
    
    if efrom == None and eto == None and eunit != None:
        print 'You gave the Enery range type keyword, but no energy range...'
        raise Exception('energy range keywords malformed')
    #~ if (efrom not None) or (eto not None):
    eunit_ref = ['el_cm1', 'eu_cm1', 'el_k', 'eu_k']
        # check that unit is given, and correct
        # or set default (eu_k)
    # set efrom if supplied
    if efrom != None:
        form['energy_rangefrom'] = str(efrom)
    # set eto if supplied
    if eto != None:
        form['energy_rangeto'] = str(eto)
    # check if eunit is given, and tick the corresponding radio
    # button, if none then assume Kelvin
    if eunit != None: #arg.has_key('efrom') or arg.has_key('eto'):
        if eunit.lower() in eunit_ref:
            pass
        else:
            print 'Energy range unit keyword \'eunit\' malformed.'
            raise Exception('eunit keyword malformed')
    else:
        # no value, assuming its in Kelvin (i.e. Eu/kb)
        eunit = 'eu_k'
    # now set the eunit radio button
    form.find_control('energy_range_type').toggle(eunit.lower())   
    return form

def  _parse_transition(form, arg):
    ### Specify Transition
    #
    if arg.has_key('transition'):
        form['tran'] = str(arg['transition'])
    return form

def _parse_line_intensity(form, lill):
    ### Line Intensity Lower Limits
    if lill != None:
        if lill[1].lower() == 'cdms_jpl':
            form.find_control('lill_cdms_jpl').disabled = False
            form['lill_cdms_jpl'] = str(lill[0])
        elif lill[1].lower() == 'sijmu2':
            form.find_control('lill_sijmu2').disabled = False
            form['lill_sijmu2'] = str(lill[0])
        elif lill[1].lower() == 'aij':
            form.find_control('lill_aij').disabled = False
            form['lill_aij'] = str(lill[0])
    return form

def _parse_frequency_error_limit(form):
    return form

def _set_settings(form):
    # these settings are so that everything will be displayed in the 
    # table then we get everything, and the user can choose AFTER if 
    # they want it or not
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
    return form

def _get_results(form, dbg = False):
    # click the form
    clicked_form = form.click()
    # then get the results page
    result = mechanize.urlopen(clicked_form)

    #### EXPORTING RESULTS FILE
    # so what I do is that I fetch the first results page,
    # click the form/link to get all hits as a colon separated
    # ascii table file
    
    # get the form
    resultform = mechanize.ParseResponse(result, backwards_compat=False)
    result.close()
    resultform = resultform[0]
    # set colon as dilimeter of the table (could use anything I guess)
    #~ resultform.find_control('export_delimiter').items[1].selected =  True
    resultform.find_control('export_delimiter').toggle('colon')
    resultform_clicked = resultform.click()
    result_table = mechanize.urlopen(resultform_clicked)
    data = result_table.read()
    result_table.close()
    if dbg:
        return resultform, result_table, data
    else:
        return data

def _parse_result(data, output='astropy.table'):
    """
    Only one output type at the moment    
    """
    if output == 'astropy.table':
        # get each line (i.e. each molecule)
        rows = data.split('\n')
        # get the names of the columns
        column_names = rows[0]
        column_names = column_names.split(':')
        
        for i in arange(len(column_names)):
            column_names[i] = column_names[i].replace('<br>', ' ')
            column_names[i] = column_names[i].replace('<sub>', '_')
            column_names[i] = column_names[i].replace('<sup>', '^')
            column_names[i] = column_names[i].replace('</sup>', '')
            column_names[i] = column_names[i].replace('</sub>', '')
            column_names[i] = column_names[i].replace('&#956;', 'mu')
            column_names[i] = column_names[i].replace('sid[0] is null', '')
        rows = rows[1:-1]
        rows = [i.split(':') for i in rows]
        rows = array(rows)
        rows[rows == ''] = 'nan'
        
        column_dtypes = ['str', 'str', 'float', 'float', 'float' , 'float' ,
                        'str', 'str', 'float',
                        'float', 'float', 'float', 'str', 'float', 'float',
                        'float', 'float', 'float', 'float','float','str']
        column_units = [None, None, 'GHz?', 'GHz?', 'GHz?', 'GHz?', None, 
                        None, '?', 'Debye^2', '?', 'log10(Aij)', '?', 
                        'cm^-1', 'K', 'cm^-1', 'K', None, None, None, None]
        
        results = Table(data = rows , 
                        names = column_names, 
                        dtypes = column_dtypes)
        
        for i in arange(len(column_units)):
            results.field(i).units = column_units[i]
        return results

