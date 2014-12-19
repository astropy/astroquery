#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
#  adslib.py
#
#  Module to search the ads
#
#  Copyright 2012 Magnus Persson <http://vilhelm.nu>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#  
#  version 0.0.1a

"""
Script to search the NASA ADS directory

Need :  o scipy
        o mechanize module (standard in Python >2.6/2.7?)
        o urllib2 module (standard Python module, required(?) by mechanize)
        o beautiful soup/xml (xml standard in Python >2.6/2.7?)

"""

"""
ADSlib - Python Module to interact with NASA ADS
at

http://adswww.harvard.edu/

OR one of the mirrors

http://cdsads.u-strasbg.fr/
http://ukads.nottingham.ac.uk/
http://esoads.eso.org/
http://ads.ari.uni-heidelberg.de/
http://ads.inasan.ru/
http://ads.mao.kiev.ua/
http://ads.astro.puc.cl/
http://ads.nao.ac.jp/
http://ads.bao.ac.cn/
http://ads.iucaa.ernet.in/
http://ads.arsip.lipi.go.id/
http://saaoads.chpc.ac.za/
http://ads.on.br/




"""

"""
----[ Change log ]----

* 2012 Dec 15 
    Code cleanup. 

* 2012 Oct 29 
    Now only uses mechanize module(!) Yay.

* 2012 Oct 02
    File created.



"""

"""
NOTES:
# advanced search query
abstract_service.html

# quick search
index.html

"""


mirrors = [
        'http://adswww.harvard.edu/',
        'http://cdsads.u-strasbg.fr/',
        'http://ukads.nottingham.ac.uk/',
        'http://esoads.eso.org/',
        'http://ads.ari.uni-heidelberg.de/'
        'http://ads.inasan.ru/',
        'http://ads.nao.ac.jp/',
        'http://ads.iucaa.ernet.in/',
        'http://ads.arsip.lipi.go.id/',
        'http://saaoads.chpc.ac.za/',
        'http://ads.on.br/'
        ]

advanced_q = 'abstract_service.html'

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
    # ie. Jørgensen, æ and åäö and ßü etc are represented by funny numbers and '\'
        
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
######## NOTES 

### FIELDS
# bibcode
# title
# authors
# score
# pubdate
# possilbe (quick)links : 
#           A Abstract 
#           C CITATIONS
#           D On-line Data
#           E EJOURNAL
#           F Printable Article
#           G Gif Images
#           H HEP/Spires Information
#           I Author Comments
#           L Library Entries
#           M Multimedia
#           N NED Objects
#           O Associated Articles
#           P PDS datasets
#           R REFERENCES
#           S SIMBAD Objects
#           T TOC
#           U Also read
#           X arXiv e-print
#           Z Abstract Custom


"""


6.3.4 - Embedded Queries

This section describes how the abstract service can be accessed from embedded forms. The URL for submitting embedded forms is: 

http://adsabs.harvard.edu/cgi-bin/abs_connect 

The syntax is: 

<a href=http://adsabs.harvard.edu/cgi-bin/abs_connect?param1=val1&param2=val2&... >...</a> 

where parami are the names of the parameters and vali are their values. There are no spaces allowed in a URL. Any blanks need to be encoded as a '+' (e.g. between author last and first names). The list of the possible parameters and their possible values is available to build queries. It is advisable to use only the more basic parameters for such queries since the more complicated parameters are more likely to change with future versions of the search system. 

One use of this is for including a link to the bibliography for a particular author in a document. 

To do so, use the following syntax: 

http://adsabs.harvard.edu/cgi-bin/abs_connect?author=last,+f.&return_req=no_params 

This sets the author=last, f, and prevents the listing of parameters at the bottom of the page (return_req=no_params). 

If you want to specify the author middle initial in addition to the first initial, use exact author matching (&aut_xct=YES). 

To build a search for two different formats of author names, enter the two author arguments separated with a semicolon. 

http://adsabs.harvard.edu/cgi-bin/abs_connect?author=last,+f.m.;last,+first+m.&aut_xct=YES&return_req=no_params 

Such a link will always provide access to the latest bibliography of an author without the need to update anything. 

Sometimes such a list includes articles by somebody else with the same name. You can exclude specific articles from the results list with the command 

exclude=bibcode1,bibcode2,... 

You can also include specific articles with the command 

include=bibcode1,bibcode2,... 

This allows for finely customized bibliographies. 



List of ADS query parameter keywords

author	list of semicolon separated authornames as last, f
object	list of semicolon separated object names
keyword	list of semicolon separated keywords
start_mon	starting month as integer (Jan == 1, Dec == 12)
start_year	starting year as integer (4 digits)
end_mon	ending month as integer (Jan == 1, Dec == 12)
end_year	ending year as integer (4 digits)
start_entry_day	start entry day of month as integer
start_entry_mon	start entry month as integer
start_entry_year	start entry year as integer
end_entry_day	start entry day of month as integer
end_entry_mon	start entry month as integer
end_entry_year	start entry year as integer
title	title words, any non-alpha-numeric character separates
text	abstract words, any non-alpha-numeric character separates
fulltext	OCRd fulltext, any non-alpha-numeric character separates
affiliation	affiliation words, any non-alpha-numeric character separates
bibcode	bibcode for partial bibcode search. If a bibcode is 
specified, no other search will be done
nr_to_return	how many abstracts to return (default is 50, max 500)
start_nr	where to start returning in list of retrieved abstracts 
default is 1
aut_wt	floating point weight for author search, default: 1.0
obj_wt	floating point weight for object search, default: 1.0
kwd_wt	floating point weight for keyword search, default: 1.0
ttl_wt	floating point weight for title search, default: 0.3
txt_wt	floating point weight for text search, default: 3.0
full_wt	floating point weight for full search, default: 3.0
aff_wt	floating point weight for affiliation search, default: 1.0
aut_syn	author synonym replacement. aut_syn="YES" turns it on (default is on)
ttl_syn	title synonym replacement. ttl_syn="YES" turns it on (default is on)
txt_syn	text synonym replacement. txt_syn="YES" turns it on (default is on)
full_syn	full text synonym replacement. full_syn="YES" turns it on (default is on)
aff_syn	affiliation synonym replacement. aff_syn="YES" turns it on (default is on)
aut_wgt	authors used for weighting. aut_wgt="YES" turns it on (default is on)
obj_wgt	objects used for weighting. obj_wgt="YES" turns it on (default is on)
kwd_wgt	keywords used for weighting. kwd_wgt="YES" turns it on (default is on)
ttl_wgt	title used for weighting. ttl_wgt="YES" turns it on (default is on)
txt_wgt	text used for weighting. txt_wgt="YES" turns it on (default is on)
full_wgt	full text used for weighting. full_wgt="YES" turns it on (default is on)
aff_wgt	affiliation used for weighting. aff_wgt="YES" turns it on (default is on)
aut_sco	authors weighted scoring. aut_sco="YES" turns it on (default is off)
kwd_sco	keywords weighted scoring. kwd_sco="YES" turns it on (default is off)
ttl_sco	title weighted scoring. ttl_sco="YES" turns it on (default is on)
txt_sco	text weighted scoring. txt_sco="YES" turns it on (default is on)
full_sco	text weighted scoring. full_sco="YES" turns it on (default is on)
aff_sco	affiliation weighted scoring. aff_sco="YES" turns it on (default is off)
aut_req	authors required for results. aut_req="YES" turns it on (default is off)
obj_req	objects required for results. obj_req="YES" turns it on (default is off)
kwd_req	keywords required for results. kwd_req="YES" turns it on (default is off)
ttl_req	title required for results. ttl_req="YES" turns it on (default is off)
txt_req	text required for results. txt_req="YES" turns it on (default is off)
full_req	text required for results. full_req="YES" turns it on (default is off)
aff_req	affiliation required for results. aff_req="YES" turns it on (default is off)
aut_logic
obj_logic
kwd_logic
ttl_logic
txt_logic
full_logic
aff_logic	Combination logic: 
xxx_logic="AND": combine with AND 
xxx_logic="OR": combine with OR (default)
xxx_logic="SIMPLE": simple logic (use +, -) 
xxx_logic="BOOL": full boolean logic 
xxx_logic="FULLMATCH": do AND query in the selected field 
and calculate the score according to how many words in 
the field of the selected reference were matched by 
the query
return_req	requested return: 
return_req="result" : return results (default) 
return_req="form" : return new query form 
return_req="no_params": return results 
set default parameters, don't display params
db_key	which database to query: db_key="AST" : Astronomy(default)
"PRE": arXiv e-prints 
"PHY": Physics, "GEN": General, CFA: CfA Preprints
atcl_only	select only OCR pages from articles
jou_pick	specify which journals to select: 
jou_pick="ALL" : return all journals (default) 
jou_pick="NO" : return only refereed journals 
jou_pick="EXCL" : return only non-refereed journals
ref_stems	list of comma-separated ADS bibstems to return, e.g. ref_stems="ApJ..,AJ..."
min_score	minimum score of returned abstracts 
(floating point, default 0.0)
data_link	return only entries with data. 
data_link="YES" turns it on, default is off
abstract	return only entries with abstracts. 
abstract="YES" turns it on, default is off
alt_abs	return only entries with alternate abstracts. 
alt_abs="YES" turns it on, default is off
aut_note	return only entries with author notes. 
aut_note="YES" turns it on, default is off
article	return only entries with articles. 
article="YES" turns it on, default is off
article_link	return only entries with electronic articles. 
article_link="YES" turns it on, default is off
simb_obj	return only entries with simbad objects. 
simb_obj="YES" turns it on, default is off
ned_obj	return only entries with ned objects. 
ned_obj="YES" turns it on, default is off
gpndb_obj	return only entries with gpndb objects. 
gpndb_obj="YES" turns it on, default is off
lib_link	return only entries with library links. 
lib_link="YES" turns it on, default is off
data_and	return only entries with all selected data available. 
data_and="ALL": no selection, return all refs (default) 
data_and="NO" : return entries with AT LEAST ONE of the 
data items selected with the above flags 
data_and="YES": return only entries that have ALL links 
selected with the above flags
version	version number for the query form
data_type	data type to return 
data_type="HTML" return regular list (default) 
data_type="PORTABLE" return portable tagged format 
data_type="PLAINTEXT" return plain text 
data_type="BIBTEX" return bibtex format 
data_type="BIBTEXPLUS" return bibtex with abstract 
data_type="ENDNOTE" return ENDNOTE format 
data_type="DUBLINCORE" return DUBLINCORE format 
data_type="XML" return XML format 
data_type="SHORT_XML" return short XML format (no abstract)
data_type="VOTABLE" return VOTable format 
data_type="RSS" return RSS format
mail_link	return only entries with mailorder. 
mail_link="YES" turns it on, default is off
toc_link	return only entries with tocorder. 
toc_link="YES" turns it on, default is off
pds_link	return only entries with pds data. 
pds_link="YES" turns it on, default is off
multimedia_link	return only entries with multimedia data. 
multimedia_link="YES" turns it on, default is off
spires_link	return only entries with spires data. 
spires_link="YES" turns it on, default is off
group_and	return only entries from all selected groups. 
group_and="ALL":no selection (default) 
group_and="NO" :return entries that are in at least one grp
group_and="YES":return only entries from ALL groups 
selected with group_bits
group_sel	which group to select, e.g. group_sel="Chandra,HST"
ref_link	return only entries with reference links. 
ref_link="YES" turns it on, default is off
citation_link	return only entries with citation links. 
citation_link="YES" turns it on, default is off
gif_link	return only entries with scanned articles links.
open_link	return only entries with open access.
aut_xct	exact author search. aut_xct="YES" turns it on
lpi_query	lpi_query="YES" query for LPI objects, default is off
sim_query	sim_query="YES" query for SIMBAD objects, default is on
ned_query	ned_query="YES" query for NED objects, default is on
iau_query	iau_query="YES" query for IAU objects, default is off
sort	sort options: 
"SCORE": sort by score 
"AUTHOR": sort by first author 
"NDATE": sort by date (most recent first 
"ODATE": sort by date (oldest first) 
"BIBCODE": sort by bibcode 
"ENTRY": sort by entry date in the database
"PAGE": sort by page number 
"RPAGE": reverse sort by page number 
"CITATIONS": sort by citation count (replaces 
score with number of citations) 
"NORMCITATIONS": sort by normalized citation count 
(replaces score with number of normalized citations) 
"AUTHOR_CNT": sort by author count
query_type	what to return: query_type=PAPERS returns regular records (default) 
query_type=CITES returns citations to selected records 
query_type=REFS returns references in selected records 
query_type=ALSOREADS returns also-reads in selected records
return_fmt	return format: return_fmt="LONG": return full abstract 
return_fmt="SHORT": return short listing (default)
type	where to return the data (screen, file, printer, etc)
defaultset	use default settings (same as ret_req=no_params 
but displays query parameters on short form)
format	Custom reference format
charset	character set for text output
year	year field for bibcode matching
bibstem	bibstem field for bibcode matching
volume	volume field for bibcode matching
page	page field for bibcode matching
associated_link	return only entries with associated articles. 
associated_link="YES" turns it on, default is off
ar_link	return only entries with AR links. 
ar_link="YES" turns it on, default is off
tables	return results with table formatting (overrides pref.)
email_ret	email_ret="YES": return query result via email
exclude	exclude=bibcode1[,bibcode2...]: exclude specified bibcodes
from results list
include	include=bibcode1[,bibcode2...]: include specified bibcodes
in results list
selectfrom	selectfrom=bibcode1[,bibcode2...]: include only bibcodes 
from specified bibcode list
RA	Right ascension for cone search
DEC	Declination for cone search
SR	Search radius for cone search (default is 10 arcmin)
method	form method of query form: GET or POST
nfeedback	number of records to use in feedback queries
doi	DOI
preprint_link	return only entries with preprint data. 
preprint_link="YES" turns it on, default is off
refstr	reference string to resolve
mimetype	mimetype of returned page (default depends on data_type)
qsearch	if set, quick search box is displayed in HTML output
arxiv_sel	which arxiv categories to select
article_sel	select only articles (not catalogs, abstracts, etc)
adsobj_query	search object names in abstract text

"""



