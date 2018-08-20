# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""

@author: Javier Duran
@contact: javier.duran@sciops.esa.int

European Space Astronomy Centre (ESAC)
European Space Agency (ESA)

Created on 13 Ago. 2018


"""

import urllib.request
from . import conf
from .handler import Handler, EhstHandler

__all__ = ['Hst', 'HstClass', 'Conf', 'conf', 'EhsdtHandler', 'Handler']

class HstClass(object):

    data_url = conf.DATA_ACTION#"http://archives.esac.esa.int/ehst-sl-server/servlet/data-action?"
    metadata_url = conf.METADATA_ACTION#"http://archives.esac.esa.int/ehst-sl-server/servlet/metadata-action?"

    def __init__(self, url_handler=None):
        if url_handler is None:
            self.__handler = Handler
        else:
            self.__handler = url_handler

    def get_product(self, observation_id, calibration_level="RAW", filename=None, verbose=False):
        """ Download products from EHST
            
            Parameters
            ----------
            observation_id : string, id of the observation to be downloaded, mandatory
            The identifier of the observation we want to retrieve, regardless of whether it is simple or composite.
            calibration_level : string, calibration level, optional, default 'RAW'
            The identifier of the data reduction/processing applied to the data. By default, the most scientifically relevant level will be chosen. RAW, CALIBRATED, PRODUCT or AUXILIARY
            filename : string, file name to be used to store the artifact, optional, default None
            File name for the observation.
            verbose : bool, optional, default 'False'
            flag to display information about the process
            
            Returns
            -------
            None. It downloads the observation indicated
        """

        obs_id = "OBSERVATION_ID=" + observation_id
        cal_level = "CALIBRATION_LEVEL=" + calibration_level
        link = self.data_url + obs_id + "&" + cal_level
        if filename is None:
            filename = observation_id + ".tar"
        print(link)
        return self.__handler.get_file(link, filename, verbose)

    def get_artifact(self, artifact_id, filename=None, verbose=False):
        """ Download artifacts from EHST
            
            Parameters
            ----------
            artifact_id : string, id of the artifact to be downloaded, mandatory
            The identifier of the physical product (file) we want to retrieve.
            filename : string, file name to be used to store the artifact, optional, default None
            File name for the artifact
            verbose : bool, optional, default 'False'
            flag to display information about the process
            
            Returns
            -------
            None. It downloads the artifact indicated
            """

        art_id = "ARTIFACT_ID=" + artifact_id
        link = self.data_url + art_id
        if filename is None:
            filename = artifact_id
        print(link)
        return self.__handler.get_file(link, filename, verbose)

    def get_postcard(self, observation_id, calibration_level="RAW", resolution=256, filename=None, verbose=False):
        """ Download postcards from EHST
            
            Parameters
            ----------
            observation_id : string, id of the observation for which download the postcard, mandatory
            The identifier of the observation we want to retrieve, regardless of whether it is simple or composite.
            calibration_level : string, calibration level, optional, default 'RAW'
            The identifier of the data reduction/processing applied to the data. By default, the most scientifically relevant level will be chosen. RAW, CALIBRATED, PRODUCT or AUXILIARY
            resolution : integer, postcard resolution, optional, default 256
            Resolution of the retrieved postcard. 256 or 1024
            filename : string, file name to be used to store the postcard, optional, default None
            File name for the artifact
            verbose : bool, optional, default 'False'
            Flag to display information about the process
            
            Returns
            -------
            None. It downloads the observation postcard indicated
        """

        retri_type = "RETRIEVAL_TYPE=POSTCARD"
        obs_id = "OBSERVATION_ID=" + observation_id
        cal_level = "CALIBRATION_LEVEL=" + calibration_level
        res = "RESOLUTION=" + str(resolution)
        link = self.data_url + retri_type + "&" + obs_id + "&" + cal_level + "&" + res
        if filename is None:
            filename = observation_id + ".tar"
        print(link)
        return self.__handler.get_file(link, filename, verbose)

    def get_metadata(self, params, filename=None, verbose=False):
        """ It executes a query over EHST and download the xml with the results
            
            Parameters
            ----------
            params : string, set of restrictions to be applied during the execution of the query, mandatory
            Set of restrictions to be applied during the execution of the query.
            calibration_level : string, calibration level, optional, default 'RAW'
            The identifier of the data reduction/processing applied to the data. By default, the most scientifically relevant level will be chosen. RAW, CALIBRATED, PRODUCT or AUXILIARY
            resolution : integer, postcard resolution, optional, default 256
            Resolution of the retrieved postcard. 256 or 1024
            filename : string, file name to be used to store the postcard, optional, default None 
            File name for the artifact
            verbose : bool, optional, default 'False'
            Flag to display information about the process
            
            Returns
            -------
            None. It downloads metadata as a result of the restrictions defined.
        """

        link = self.metadata_url + params
        if filename is None:
            filename = "metadata.xml"
        print(link)
        return self.__handler.get_file(link, filename, verbose)

Hst = HstClass()
