# -*- coding: utf-8 -*-
# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import print_function

# put all imports organized as shown below
# 1. standard library imports

# 2. third party imports
import astropy.units as u
import astropy.coordinates as coord
import astropy.io.votable as votable
from astropy.table import Table
from astropy.io import fits
from bs4 import BeautifulSoup

# 3. local imports - use relative imports
# commonly required local imports shown below as example
from ..query import BaseQuery # all Query classes should inherit from this.
from ..utils import commons # has common functions required by most modules
from ..utils import prepend_docstr_noreturns # automatically generate docs for similar functions
from ..utils import async_to_sync # all class methods must be callable as static as well as instance methods.
from . import conf # import configurable items declared in __init__.py


# export all the public classes and methods
__all__ = ['Ads', 'AdsClass']

# declare global variables and constants if any


# Now begin your main class
# should be decorated with the async_to_sync imported previously
@async_to_sync
class AdsClass(BaseQuery):
    """
    Query the NASA Astronomical Data Service

    """
    # use the Configuration Items imported from __init__.py to set the URL, TIMEOUT, etc.
    URL = conf.server + "cgi-bin/nph-abs_connect"
    TIMEOUT = conf.timeout

    def query(self, name, get_query_payload=False, verbose=False, **kwargs):
        """
        This method is for services that can parse object names.

        Example URL:
            http://adsabs.harvard.edu/cgi-bin/nph-abs_connect?db_key=AST&db_key=PRE&qform=AST&arxiv_sel=astro-ph&arxiv_sel=cond-mat&arxiv_sel=cs&arxiv_sel=gr-qc&arxiv_sel=hep-ex&arxiv_sel=hep-lat&arxiv_sel=hep-ph&arxiv_sel=hep-th&arxiv_sel=math&arxiv_sel=math-ph&arxiv_sel=nlin&arxiv_sel=nucl-ex&arxiv_sel=nucl-th&arxiv_sel=physics&arxiv_sel=quant-ph&arxiv_sel=q-bio&sim_query=YES&ned_query=YES&adsobj_query=YES&aut_logic=OR&obj_logic=OR&author=%5Edale&object=&start_mon=&start_year=&end_mon=&end_year=&ttl_logic=OR&title=&txt_logic=OR&text=&nr_to_return=200&start_nr=1&jou_pick=ALL&ref_stems=&data_and=ALL&group_and=ALL&start_entry_day=&start_entry_mon=&start_entry_year=&end_entry_day=&end_entry_mon=&end_entry_year=&min_score=&sort=SCORE&data_type=SHORT&aut_syn=YES&ttl_syn=YES&txt_syn=YES&aut_wt=1.0&obj_wt=1.0&ttl_wt=0.3&txt_wt=3.0&aut_wgt=YES&obj_wgt=YES&ttl_wgt=YES&txt_wgt=YES&ttl_sco=YES&txt_sco=YES&version=1

        Parameters
        ----------
        name : str
            name of the author to query.
        get_query_payload : bool, optional
            This should default to False. When set to `True` the method
            should return the HTTP request parameters as a dict.
        verbose : bool, optional
           This should default to `False`, when set to `True` it displays
           VOTable warnings.
        any_other_param : <param_type>
            similarly list other parameters the method takes

        Returns
        -------
        result : `~astropy.table.Table`
            The result of the query as a `~astropy.table.Table` object.
            All queries other than image queries should typically return
            results like this.

        Examples
        --------
        While this section is optional you may put in some examples that
        show how to use the method. The examples are written similar to
        standard doctests in python.
        """

        # typically query should have the following steps:
        # 1. call the corresponding query_async method, and
        #    get the HTTP response of the query
        # 2. check if 'get_query_payload' is set to True, then
        #    simply return the dict of HTTP request parameters.
        # 3. otherwise call the parse_result method on the
        #    HTTP response returned by query_async and
        #    return the result parsed as astropy.Table
        # These steps are filled in below, but may be replaced
        # or modified as required.

        response = self.query_async(name,
                                           get_query_payload=get_query_payload,
                                           **kwargs)
        if get_query_payload:
            return response
        result = self._parse_result(response, verbose=verbose)
        return result

    # all query methods usually have a corresponding async method
    # that handles making the actual HTTP request and returns the
    # raw HTTP response, which should be parsed by a separate
    # parse_result method. Since these async counterparts take in
    # the same parameters as the corresponding query methods, but
    # differ only in the return value, they should be decorated with
    # prepend_docstr_noreturns which will automatically generate
    # the common docs. See below for an example.

    @prepend_docstr_noreturns(query.__doc__)
    def query_async(self, name, get_query_payload=False, **kwargs):
        """
        Returns
        -------
        response : `requests.Response`
            The HTTP response returned from the service.
            All async methods should return the raw HTTP response.
        """
        # the async method should typically have the following steps:
        # 1. First construct the dictionary of the HTTP request params.
        # 2. If get_query_payload is `True` then simply return this dict.
        # 3. Else make the actual HTTP request and return the corresponding
        #    HTTP response
        # All HTTP requests are made via the `commons.send_request` method.
        # This uses the Python Requests library internally, and also takes
        # care of error handling.
        # See below for an example:

        # first initialize the dictionary of HTTP request parameters
        request_payload = self._args_to_payload(name, **kwargs)

        # Now fill up the dictionary. Here the dictionary key should match
        # the exact parameter name as expected by the remote server. The
        # corresponding dict value should also be in the same format as
        # expected by the server. Additional parsing of the user passed
        # value may be required to get it in the right units or format.
        # All this parsing may be done in a separate private `_args_to_payload`
        # method for cleaner code.

        # similarly fill up the rest of the dict ...

        if get_query_payload:
            return request_payload
        # commons.send_request takes 4 parameters - the URL to query, the dict of
        # HTTP request parameters we constructed above, the TIMEOUT which we imported
        # from __init__.py and the type of HTTP request - either 'GET' or 'POST', which
        # defaults to 'GET'.
        response = self._request(method='POST',
                                 url=self.URL,
                                 data=request_payload,
                                 timeout=self.TIMEOUT)
        return response



    # as we mentioned earlier use various python regular expressions, etc
    # to create the dict of HTTP request parameters by parsing the user
    # entered values. For cleaner code keep this as a separate private method:

    def _args_to_payload(self, name=None, *args, **kwargs):
        request_payload = dict()
        if name is not None:
            request_payload['author'] = name
        request_payload.update(kwargs)
        # code to parse input and construct the dict
        # goes here. Then return the dict to the caller
        return request_payload

    # the methods above call the private _parse_result method.
    # This should parse the raw HTTP response and return it as
    # an `astropy.table.Table`. Below is the skeleton:

    def _parse_result(self, response, verbose=False):
        # start parsing the results
        t = BeautifulSoup(response.content)
        tables = t.findAll('table')

        r = tables[1].findAll('td')[0]
        y = r.findAll('strong')[0].contents[0]
        nres = int(y)
        if nres<1:
            import ipdb; ipdb.set_trace()

        # get table with results
        resulttable = tables[2]
        # get the rows of the table
        rows = resulttable.findAll('tr')
        # get each result entry per list item
        # Why 57?
        entries = [rows[i:i+3][1:] for i in range(2,57,3)][:-1]

        ############################################
        ######## GET RESULTLIST

        ###### the problem with this is that web is in UNICODE,
        # ie. Jørgensen, æ and åäö and ßü etc are represented by funny numbers and '\'

        #resultlist = [_Result(i) for i in entries]
        return _Resultlist(entries)

class _Resultlist(object):
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
    def __repr__(self):
        return self.__str__()

class _Result(object):
    """
    Internal object to represent each result
    """
    def __init__(self, entry):
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

        self.authors = [i.split(',') for i in authors]
        self.author = ', '.join(self.authors[0])
    def __repr__(self):
        return repr([self.author, self.authors, self.title, self.url_abstract_page, self.ads_score, self.links, self.bibcode, self.pubdate])
    def _returnlist_(self):
        return [self.author, self.authors, self.title, self.url_abstract_page,
                self.ads_score, self.links, self.bibcode, self.pubdate]


# the default tool for users to interact with is an instance of the Class
Ads = AdsClass()

# once your class is done, tests should be written
# See ./tests for examples on this

# Next you should write the docs in astroquery/docs/module_name
# using Sphinx.
