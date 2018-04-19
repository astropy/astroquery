 # put all imports organized as shown below
 # 1. standard library imports

# urlparse package just to Python 2.x
from bs4 import BeautifulSoup
import urllib
import requests
import urlparse
from unicodedata import normalize

# 2. third party imports

import astropy.units as u
from astropy.table import Table

class RMS_by_coordinates():
  """
  Class to The RMS Cone Search by COORDINATE
  Required:
  
  coordinates (19:27:42.1 16:37:25.0) ; [string] ; coordinates
  
  Inputs with default value:
  
  Search radius (arcsec) ;  [float]  ; por defecto 60 ; radius
  Radio button           ;  [integer in range[1,4] ]: ; list_id
    - Final RMS   ; value = 1 selected 
    - Near/Mid-IR ; value = 2
    - Rejected    ; value = 3
    - MSX Colour  ; value = 4 
  """

  def __init__(self,coordinates,radius,list_id):
    self.dd_query   = {'text_field_1':coordinates,'radius_field':radius,'list_id':list_id}
    self.result_soup = self.__get_soup()

  def __open_session(self):
    session       = requests.Session()
    base_response = session.get('http://rms.leeds.ac.uk/cgi-bin/public/RMS_CONE_SEARCH.cgi')
    if not base_response.status_code == 200:
      print 'HTTP 404 Not Found, the url may have changed'
      return 0 
      pass
    else:
      print 'Successful connection'
      return session

  def __get_soup(self):
    session = self.__open_session()
    if session == 0:
      return 0 
    else:
      result_send_query = session.post('http://rms.leeds.ac.uk/cgi-bin/public/RMS_SEARCH_RESULTS.cgi',data=self.dd_query)
      result_soup       = BeautifulSoup(result_send_query.text,'html.parser')
      return result_soup

  def __scrape_forms(self,form):
    for tr in form.find_all('tr'):
      return [td.text for td in tr.find_all('td')]

  def get_RMS_by_coordinates(self):
    if self.result_soup == 0:
      print 'Sorry'
      return 0 
    else:
      columns      = [th.text.strip() for th in self.result_soup.find_all('th')][:-1]
      result_query = self.result_soup.find("div",{"id":"content"}).find_all_next('form')
      d_results    = {i:self.__scrape_forms(form) for i,form in enumerate(result_query)}
      res_table    = Table(rows=d_results.values(),names=columns,dtype=('S','S','S','S','f'))
      return res_table


class RMS_by_name():
  """
  Class to The RMS Cone Search by NAME
  Required:
  coordinates (19:27:42.1 16:37:25.0) ; [string] ; coordinates
  Inputs with default value:
  Search radius (arcsec) ;  [float]  ; por defecto 60 ; radius
  Radio button           ;  [integer in range[1,4] ]: ; list_id
    - Final RMS   ; value = 1 selected 
    - Near/Mid-IR ; value = 2
    - Rejected    ; value = 3
    - MSX Colour  ; value = 4 
  """
  def __init__(self,coordinates,radius,list_id):
    self.dd_query   = {'text_field_1':coordinates,'radius_field':radius,'list_id':list_id}
    self.result_soup = self.__get_soup()



  def __open_session(self):
    session       = requests.Session()
    base_response = session.get('http://rms.leeds.ac.uk/cgi-bin/public/RMS_CONE_SEARCH.cgi')
    if not base_response.status_code == 200:
      print 'HTTP 404 Not Found, the url may have changed'
      return 0 
      pass
    else:
      print 'Successful connection'
      return session

  def __get_soup(self):
    session = self.__open_session()
    if session == 0:
      return 0 
    else:
      result_send_query = session.post('http://rms.leeds.ac.uk/cgi-bin/public/RMS_SEARCH_RESULTS.cgi',data=self.dd_query)
      result_soup       = BeautifulSoup(result_send_query.text,'html.parser')
      return result_soup

  def __scrape_forms(self,form):
    for tr in form.find_all('tr'):
      return [td.text for td in tr.find_all('td')]
  
  
  # ======== ========= ============
  
  def get_table(self,h3_title):
    """
    # =========================== #
      Method to get table of records
    # =========================== #
    This method does not work with all table of records !!
    Only to:
      # MSX and IRAS Details 
      - MSX_Point_Source_Position_and_Fluxes
      - Associated_IRAS_Point_Source
      
      # Mid-Infrared Data
      - Glimpse_Point_Sources
      - WISE_Point_Source_Position_and_Fluxes
      
      # (Sub)mm Continuum Data 
      - Sub_mm_Catalogue_Parameters
      
      # Radio Continuum Results 
      - Radio_Catalogue_Search_Results
      
      # Far-Infrared Data
      - Far_infrared_Fluxes_for_RMS_sources
      
     Parameters
     ----------
     h3_title: str
      h3 name referring to the table of records
    """
    caption = self.result_soup.find("caption",string=h3_title)
    print caption
    table_info  = caption.find_previous('table')
    return table_info
    

  def scraper_text_tables(self,table,i=1):
    """
    # =============================== #
      Method to scraper table of records
    # =============================== #
    
    This method does not work with all table of records !!
    Only to:
      # MSX and IRAS Details 
      - MSX_Point_Source_Position_and_Fluxes
      - Associated_IRAS_Point_Source
      
      # Mid-Infrared Data
      - Glimpse_Point_Sources
      - WISE_Point_Source_Position_and_Fluxes
      
      # (Sub)mm Continuum Data 
      - Sub_mm_Catalogue_Parameters
      
      # Radio Continuum Results 
      - Radio_Catalogue_Search_Results
    Parameters
    ----------
    table: bs4.element.Tag
       Table of records
    """
    columns = []
    td_info = {}
    for tr in table.find_all('tr'):
        if ((len(tr.find_all('th')) != 0) & (len(columns) == 0)):
            columns = [th.text.strip() for th in tr.find_all('th')]
            pass
        elif ((len(tr.find_all('th')) != 0)):
            td_info['Units'] = [th.text for th in tr.find_all('th')]
            pass
        else:
            td_info[i] = [td.text for td in tr.find_all('td')]
            i += 1
            pass
    try:
      res_table    = Table(rows=td_info.values(),names=columns)
    except ValueError:
      columns = [normalize('NFKD', t).encode('ascii','ignore').replace(' m',' mu_m') for t in columns]
      res_table    = Table(rows=td_info.values(),names=columns)
    #df = pd.DataFrame.from_dict(td_info,orient='index')
    #df.columns = columns
    return res_table
  # ========== MSX_IRAS ================ #

  def get_MSX_Point_Source_Position_and_Fluxes(self):
    """
    Method to scraper MSX Point Source Position and Fluxes Table
    
    Return
    ------
    pd.DataFrame if exist table of records to MSX Point Source Position and Fluxes 
    str          if not exist table
    """
    table_info = self.get_table('MSX Point Source Position and Fluxes')
    if type(table_info) != type(None):
      MSX_info = self.scraper_text_tables(table_info)
      pass
    else:
      MSX_info = 'No info'
      pass
    return MSX_info
    
  def  get_Associated_IRAS_Point_Source(self):
    """
    Method to scraper Associated IRAS Point Sourc Table
    
    Return
    ------
    pd.DataFrame if exist table of records to Associated IRAS Point Sourc Table
    str          if not exist table
    """
    table_info = self.get_table(' Associated IRAS Point Source(s)')
    if type(table_info) != type(None):
      Asc_IRAS_info = self.scraper_text_tables(table_info)
      pass
    else:
      Asc_IRAS_info = 'No info'
      pass
    return Asc_IRAS_info
    
    # ========== Near-Infrared Data ============== #
    
  def get_2MASS_Point_Source(self):
    """
    Method to scraper 2MASS Point Source(s) Table
    
    Return
    ------
    pd.DataFrame if exist table of records to 2MASS Point Source(s) 
    str          if not exist table
    """
    columns = [td.text for td in self.result_soup.find("h3",string=" Near-Infrared Spectra  ").find_previous("table").find('tr').find_all('th')]
    ems = self.result_soup.find_all("em")
    if len(ems) != 0:
      info_2MASS = {i:[td.text for td in em.find_previous('tr').find_all('td')] for i,em in enumerate(ems)}
      try:
        _2MASS_info = Table(rows=info_2MASS.values(),names=columns)
      except ValueError:
        columns = [normalize('NFKD', t).encode('ascii','ignore').replace(' m',' mu_m') for t in columns]
        _2MASS_info = Table(rows=info_2MASS.values(),names=columns)
      pass
    else:
      _2MASS_info = 'No info'
      pass
    return _2MASS_info
    
    # ========= Mid-Infrared Data =========== #
    
  def get_Glimpse_Point_Sources(self):
    """
    Method to scraper Glimpse Point Sources Table
    
    Return
    ------
    pd.DataFrame if exist table of records to Glimpse Point Sources Table
    str          if not exist table
    """
    table_info = self.get_table(' Glimpse Point Sources')
    if type(table_info) != type(None):
      Glimpse_info = self.scraper_text_tables(table_info)
      pass
    else:
      Glimpse_info = 'No info'
      pass
    return Glimpse_info
    
  def get_WISE_Point_Source_Position_and_Fluxes(self):
    """
    Method to scraper  WISE Point Source Position and Fluxe Table
    
    Return
    ------
    pd.DataFrame if exist table of records to WISE Point Source Position and Fluxe Table
    str          if not exist table
    """
    table_info = self.get_table('WISE Point Source Position and Fluxes')
    if type(table_info) != type(None):
      WISE_info = self.scraper_text_tables(table_info)
      pass
    else:
      WISE_info = 'No info'
      pass
    return WISE_info
  
  # ======== (Sub)mm Continuum Data  ======== #
  
  def get_Sub_mm_Catalogue_Parameters(self):
    """
    Method to scraper Sub mm Catalogue Parameters Table
    
    Return
    ------
    pd.DataFrame if exist table of records to Sub mm Catalogue Parameters Table
    str          if not exist table
    """
    table_info = self.get_table(' Catalogue Parameters')
    if type(table_info) != type(None):
      Sub_mm_info = self.scraper_text_tables(table_info)
      pass
    else:
      Sub_mm_info = 'No info'
      pass
    return Sub_mm_info
    
  # ======= Radio Continuum Results  ======== #
  def get_Radio_Catalogue_Search_Results(self):
    """
    Method to scraper Radio Catalogue Search Results Table
    
    Return
    ------
    pd.DataFrame if exist table of records to Radio Catalogue Search Results Table
    str          if not exist table
    """
    table_info = self.get_table('Source position and flux')
    if type(table_info) != type(None):
      RCS_info = self.scraper_text_tables(table_info)
      pass
    else:
      RCS_info = 'No info'
    return RCS_info
  
  # =======   Far-Infrared Data   ======= #
  
  def get_Far_infrared_Fluxes_for_RMS_sources(self):
    """
    Method to scraper Far infrared Fluxes for RMS sources Table
    
    Return
    ------
    pd.DataFrame if exist table of records to Far infrared Fluxes for RMS sources Table
    str          if not exist table
    """
    table_info = self.get_table(' Far-infrared Fluxes for RMS sources')
    trs = table_info.find_all('tr')
    if len(trs) == 0:
      FIF_info = 'No info'
      pass
    elif len(trs) == 1:
      columns = [th.text for th in trs[0].find_all('th')]
      tds     = [td.text.strip() for td in table_info.find_all('td')]
      td_info = [tds[i:i+len(columns)] for i in range(0, len(tds), len(columns))] 
      d_info  = {i:td_info[i] for i in range(len(td_info))}
      try:
        FIF_info = Table(rows=d_info.values(),names=columns)
      except ValueError:
        columns = [normalize('NFKD', t).encode('ascii','ignore').replace(' m',' mu_m') for t in columns]
        FIF_info = Table(rows=d_info,names=columns)
      pass
    elif len(trs) > 1:
      FIF_info = self.scraper_text_tables(table_info)
      pass
    return FIF_info
