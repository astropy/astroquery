 # put all imports organized as shown below
 # 1. standard library imports

# urlparse package just to Python 2.x
from bs4 import BeautifulSoup
import urllib
import requests
import urlparse
import pandas as pd

# 2. third party imports

import astropy.units as u

@async_to_sync
class RMS_by_coordinates(BaseQuery):
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
  request_payload['text_field_1'] = coordinates
  request_payload['radius_field'] = radius
  request_payload['listID']       = list_id
  
  session       = requests.Session()
  base_response = S.get('http://rms.leeds.ac.uk/cgi-bin/public/RMS_CONE_SEARCH.cgi')
  
  result_send_query = session.post('http://rms.leeds.ac.uk/cgi-bin/public/RMS_SEARCH_RESULTS.cgi',data=request_payload)
  
  resut_soup = BeautifulSoup(result_send_query.text,'html.parser')
  
  # Create a list with the column names of the records table
  columns = [th.text.strip() for th in resut_soup.find_all('th')][:-1]
  result_query = soup.find("div",{"id":"content"}).find_all_next('form')
  
  df_query = pd.DataFrame.from_dict({i:scrape_forms(form) for i,form in enumerate(res)},orient='index')
  df_query.colums = columns
  return df_query


  


@async_to_sync
class RMS_by_name(BaseQuery):
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
    request_payload['text_field_1'] = coordinates
    request_payload['radius_field'] = radius
    request_payload['listID']       = list_id
    
    session = requests.Session()
    base_response = S.get('http://rms.leeds.ac.uk/cgi-bin/public/RMS_CONE_SEARCH.cgi')
    
    result_send_query = session.post('http://rms.leeds.ac.uk/cgi-bin/public/RMS_SEARCH_RESULTS.cgi',data=request_payload)
    result_soup = BeautifulSoup(result_send_query.text,'html.parser')
    
    
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
        caption = result_soup.find("caption",string=h3_title)
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

        df = pd.DataFrame.from_dict(td_info,orient='index')
        df.columns = columns
        return df
      
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
        if type(table_info) != NoneType:
          MSX_info = self.scrap_text_tables(table_info)
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
        if type(table_info) != NoneType:
          Asc_IRAS_info = self.scrap_text_tables(table_info)
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
        columns = [td.text for td in result_soup.find("h3",string=" Near-Infrared Spectra  ").find_previous("table").find('tr').find_all('th')]
        ems = result_soup.find_all("em")
        if len(ems) != 0:
          info_2MASS = {i:[td.text for td in em.find_previous('tr').find_all('td')] for i,em in enumerate(ems)}
          _2MASS_info = pd.DataFrame.from_dict(info_2MASS,orient='index')
          _2MASS_info.columns = columns
          pass
        else:
          _2MASS_info = 'No info'
          pass
        return df_info
      
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
        if type(table_info) != NoneType:
          Glimpse_info = self.scrap_text_tables(table_info)
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
        if type(table_info) != NoneType:
          WISE_info = self.scrap_text_tables(table_info)
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
        if type(table_info) != NoneType:
          table_info = self.get_table(' Catalogue Parameters')
          pass
        else:
          Sub_mm_info = self.scrap_text_tables(table_info)
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
        if type(table_info) != NoneType:
          RCS_info = self.scrap_text_tables(table_info)
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
          FIF_info = pd.DataFrame.from_dict(d_info,orient='index')
          FIF_info.columns = columns
          pass
        elif len(trs) > 1:
          FIF_info = self.scrap_text_tables(table_info)
          pass
        return FIF_info
  
