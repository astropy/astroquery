# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Module to search the SAO/NASA Astrophysics Data System

:author: Magnus Persson <magnusp@vilhelm.nu>

"""

#~ import warnings
# example warning 
# warnings.warn("Band was specified, so blabla is overridden")
#~ from astropy.io import ascii
#~ from astropy import units as u
from ..query import BaseQuery
#~ from ..utils import commons, async_to_sync
from ..utils.docstr_chompers import prepend_docstr_noreturns
from . import conf

from ..utils.class_or_instance import class_or_instance
from ..utils import commons, async_to_sync


__all__ = ['ADS', 'ADSClass']
#~ 
#~ 
@async_to_sync
class ADSClass(BaseQuery):
    
    ####### FROM SPLATALOGUE
    SERVER = conf.server
    QUERY_ADVANCED_PATH = conf.advanced_path
    QUERY_SIMPLE_PATH = conf.simple_path
    TIMEOUT = conf.timeout
    
    QUERY_SIMPLE_URL = SERVER + QUERY_SIMPLE_PATH
    QUERY_ADVANCED_URL = SERVER + QUERY_ADVANCED_PATH

    ######## FROM API DOCS
    def __init__(self, *args):
        """ set some parameters """
        pass
    
    @class_or_instance
    def query_simple(self, query_string, get_query_payload=False):
        
        request_payload = self._args_to_payload(query_string)
        
        response = commons.send_request(self.QUERY_SIMPLE_URL, request_payload, self.TIMEOUT)

        # primarily for debug purposes, but also useful if you want to send
        # someone a URL linking directly to the data
        if get_query_payload:
            return request_payload

        return response

    def _parse_result(self, result):
        # do something, probably with regexp's
        return result

    def _args_to_payload(self, query_string):
        # convert arguments to a valid requests payload
        # i.e. a dictionary
        return {'qsearch' : query_string}





ADS = ADSClass()

#~ 
    #~ # global constant, not user-configurable
    #~ def __init__(self, **kwargs):
        #~ """
        #~ Initialize a ADS query class with default arguments set.
        #~ Any default keyword arguments (see `query_lines`) can be 
        #~ overridden here.
        #~ """
        #~ self.data = self._default_kwargs()
        #~ self.set_default_options(**kwargs)
    #~ 
    #~ def set_default_options(self, **kwargs):
        #~ """
        #~ Modify the default options.
        #~ """
        #~ self.data.update(self._parse_kwargs(**kwargs))
    #~ 
    #~ def _default_kwargs(self):
        #~ kwargs = dict()
        #~ return self._parse_kwargs(**kwargs)
#~ 
    #~ def _parse_kwargs(self, search=""):
        #~ """
        #~ The ADS service returns.
        #~ 
        #~ Parameters
        #~ ----------
        #~ 
        #~ Other Parameters
        #~ ----------------
        #~ 
        #~ Returns
        #~ -------
        #~ Dictionary of the parameters to send to the SPLAT page
        #~ payload : dict
            #~ A dictionary of keywords
        #~ """
#~ 
        #~ payload = { 'qsearch': search }
#~ 
        #~ return payload
#~ 
    #~ def _validate_simple_kwargs(self, search=None, **kwargs):
        #~ """
        #~ Check that a simple search query is input
        #~ """
        #~ if search is None:
            #~ raise ValueError("Must specify a search string.")
    #~ 
    #~ @prepend_docstr_noreturns("\n" + _parse_kwargs.__doc__)
    #~ def query_simple_async(self, search, **kwargs):
        #~ """
        #~ Returns
        #~ -------
        #~ response : `requests.Response`
            #~ The response of the HTTP request.
        #~ """
        #~ # have to chomp this kwd here...
        #~ get_query_payload = (kwargs.pop('get_query_payload')
                             #~ if 'get_query_payload' in kwargs
                             #~ else False)
        #~ self._validate_kwargs(simple, **kwargs)
#~ 
        #~ if hasattr(self, 'data'):
            #~ data_payload = self.data.copy()
            #~ data_payload.update(self._parse_kwargs(min_frequency=min_frequency,
                                                   #~ max_frequency=max_frequency,
                                                   #~ **kwargs))
        #~ else:
            #~ data_payload = self._default_kwargs()
            #~ data_payload.update(self._parse_kwargs(min_frequency=min_frequency,
                                                   #~ max_frequency=max_frequency,
                                                   #~ **kwargs))
#~ 
        #~ if get_query_payload:
            #~ return data_payload
#~ 
        #~ response = commons.send_request(
            #~ self.QUERY_URL,
            #~ data_payload,
            #~ self.TIMEOUT)
#~ 
        #~ self.response = response
#~ 
        #~ return response    




########################################################################






def search(query, **kwargs):
    """
    query       :  Normal string to ADS
                   or dictionary for advanced search
    
    """
    
    
    ### test code to get it up and running
    
    # main access
    # TODO : either access via Z39.50 or via URLlib/mecahnise etc
    
    # wishlist
    # TODO : simple search
    # TODO : advanced search
    # TODO : browse
    
    
    import locale
    # this reads the environment and inits the right locale
    locale.setlocale(locale.LC_ALL, "")
    
    
    try:
        # the mechanize module exports urllib2 as well...
        import mechanize
        import urllib
    except (ImportError):
        print 'You need the \"mechanize\" and urllib module'
        ' for this script to work.'
    
    try:
        from BeautifulSoup import BeautifulSoup as bfs
    except (ImportError):
        print 'You need the BeautifulSoup module...'
    
    
    import scipy
    import sys
    
    #from string import lower, upper
    # search URL
    # http://adsabs.harvard.edu/cgi-bin/nph-basic_connect?qsearch=The+Search+String
    
    # to parse the search string from "The Search String" to "The+Search+String"
    # urllib.quote(url, safe=":/")
    
    ############################################
    ######## GET THE FORM
    
    #~  Ping to know which server to use.
    working_mirror = 0
    
    got_reply = 0
    while not got_reply:
       try:
           # try to get the form
           response = mechanize.urlopen(mirrors[working_mirror] + types_q[search_type])
       except mechanize.URLError:
           # if we can't get it, try another mirror
           if not i < len(mirrors):
               break
           else:
               working_mirror += 1
           pass
       else:
           got_reply = True
    
    if not got_reply and working_mirror >= len(mirrors):
           # TODO log output
           sys.stderr.write('ERROR :  You have to be connected to the internet to access the NASA ADS database and it has to be online (on all mirrors).')
    else:
            # TODO log output
        print ('got reply from : {0}'.format(mirrors[working_mirror]))
    
    
    
    
    #~  Then check if going for the advanced interface.
    #~ advanced = int((type(query) == type({}))
    if 'advanced' in kwargs:
        # ADVANCED QUERY 
        #
        # Should I use http://adsabs.harvard.edu/abstract_service.html
        # or the full ADS Labs?
        response = mechanize.urlopen(mirrors[working_mirror] + advanced_q)
        forms = mechanize.ParseResponse(response, backwards_compat=False)
        response.close()
        form = forms[0]
        #~ if arg.has_key('dbg_snd_form'): # for test purposes
        #~ return form
        #~ form['qsearch'] = '^Persson 2012'
        
        ######## SUBMIT FORM
        #~ clicked_form = form.click()
        
        #~ result = mechanize.urlopen(clicked_form)
        
        pass
        
    elif not 'advanced' in kwargs:
        # SIMPLE QUERY 
        baseurl = (mirrors[working_mirror] + 
        'cgi-bin/nph-basic_connect?qsearch=')
        
        result = mechanize.urlopen( urllib.quote(baseurl + query, safe = ":/=?^") )
        # test below
        data = urllib.urlencode({'qsearch' : '^Persson'})
        baseurl = (mirrors[working_mirror] + 
        'cgi-bin/nph-basic_connect?')
        f = urllib.urlopen(baseurl, data)
    ############################################
    ######## PARSE RESULTS
    
    page = result.readlines()
    result.close()
    
    # start parsing the results
    t = bfs(' '.join(page))
    tables = t.findAll('table')
    
    r = tables[1].findAll('td')[0]
    y = r.findAll('strong')[0].contents[0]
    nres = int(y)
    if nres<1:
        return 0
    
    # get table with results
    resulttable = tables[2]
    # get the rows of the table
    rows = resulttable.findAll('tr')
    # get each result entry per list item
    entries = [rows[i:i+3][1:] for i in scipy.arange(2,57,3)][:-1]

    ############################################
    ######## GET RESULTLIST

    ###### the problem with this is that web is in UNICODE, 
    # ie. special chars are represented by funny numbers and '\'
        
    #resultlist = [_Result(i) for i in entries]
    return _Resultlist(entries)


############################################
######## DEFINE RESULT(S) OBJECT


class _Resultlist:
    """
    Internal object to represent the result list
    """
    def __init__(self, entries):
        self.resultlist = [_Result(i) for i in entries]
    def sort(self,sortkey = 'author', reverse_bool = False):
        from operator import itemgetter, attrgetter
        #~ sorted(resultlist, key=attrgetter('author'), reverse=True)
        return sorted(self.resultlist, key=attrgetter(sortkey), reverse = reverse_bool)
    def __str__(self):
        printlist = []
        for i in self.resultlist[:-1]:
            printlist.append('Author : {0.author}\n' 
            'Title : {0.title}\n' 
            'Score : {0.ads_score}\n'.format(i))
        return '\n'.join(printlist)

class _Result:
    """
    Internal object to represent each result
    """
    def __init__(self, entry):
    #~ def __init__(self, author, 
                        #~ authors, 
                        #~ title, 
                        #~ score, 
                        #~ bibcode,
                        #~ pubdate,
                        #~ links):
        #~ self.author = author
        #~ self.authorlist = authors
        #~ self.title = title
        #~ self.score = score
        #~ self.bibcode = bibcode
        #~ self.pubdate = pubdate  # parse?
        #~ self.links = links      # dictionary of all the links
        #
        td_tags0 = entry[0].findAll('td')
        self.bibcode = td_tags0[1].findAll('input')[0]['value'].encode('UTF-8')
        self.url_abstract_page = td_tags0[1].findAll('a')[0]['href'].encode('UTF-8')
        self.ads_score = float(td_tags0[3].contents[0].encode('UTF-8'))
        self.rank = 100 - self.ads_score
        self.pubdate = td_tags0[4].contents[0].string.encode('UTF-8')
        self.pubday = self.pubdate[:2]
        self.pubyear = self.pubdate[3:]
        #
        self.links = dict()
        for link in td_tags0[5].findAll('a'):
            self.links[link.string.encode()] = link['href'].encode('UTF-8')
        #
        td_tags1 = entry[1].findAll('td')
        
        # second part of the result entry
        self.title = td_tags1[3].contents[0].string.encode('UTF-8')
        # still in unicode
        # TODO need to convert to normal UTF, not unicode
        authors = td_tags1[1].contents[0].encode('UTF-8').split(';')
        if authors[-1] == ' ':
            # so, if the last entry in the authorlist is empty, means
            # it split a ';', which in turn means there are more 
            # authors, need to add that part...
            authors[-1] = td_tags1[1].contents[1].contents[0].encode('UTF-8') + ', COAuth'
        #
        self.authors = [i.split(',') for i in authors]
        self.author = ', '.join(self.authors[0])
        #
        #~ self.
    def __repr__(self):
        return repr([self.author, self.authors, self.title, self.url_abstract_page, self.ads_score, self.links, self.bibcode, self.pubdate])
    def _returnlist_(self):
        return [self.author, self.authors, self.title, self.url_abstract_page, self.ads_score, self.links, self.bibcode, self.pubdate]

#~ # second part of the result entry
#~ title = td_tags1[3].contents[0].string.replace(u'\xa0', u' ').encode()
#~ # still in unicode
#~ # TODO need to convert to normal UTF, not unicode
#~ authors = td_tags1[1].string.replace(u'\xa0', u' ').encode().split(';')
#~ authors = [i.split(',') for i in authors]
#~ author = authors[0]




############################################
######## RETURN SORTABLE OBJECT LIST

############################################
######## HOW TO SORT RESULTS
# needs Python 2.6 at least
#~ from operator import itemgetter, attrgetter
#~ 
#~ # now to sort it, just use one of the keys
#~ # score, high to low
#~ sorted(resultlist, key=attrgetter('author'), reverse=True)
#~ 
#~ # cmp=locale.strcoll new and untested addition
#~ 
#~ # authors alphabetical order first and then by score
#~ # i.e. sort by score if same first author
#~ sorted(resultlist, key=attrgetter('ads_score','authors'), reverse=True)
########################################################################
