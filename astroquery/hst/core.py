# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""

@author: Javier Duran
@contact: javier.duran@sciops.esa.int

European Space Astronomy Centre (ESAC)
European Space Agency (ESA)

Created on 13 Ago. 2018


"""
from astroquery.utils import commons
from astropy import units
from astropy.units import Quantity

import urllib.request
from . import conf
from astroquery.utils.tap.core import TapPlus

__all__ = ['Hst', 'HstClass', 'Conf', 'conf', 'EhsdtHandler', 'Handler']


class EhstHandler(object):

    def __init__(self):
        return

    def get_file(self, url, filename, verbose=False):
        urllib.request.urlretrieve(url, filename)
        return

Handler = EhstHandler()


class HstClass(object):

    data_url = conf.DATA_ACTION
    metadata_url = conf.METADATA_ACTION

    def __init__(self, url_handler=None, tap_handler=None):
        if url_handler is None:
            self.__handler = Handler
        else:
            self.__handler = url_handler
            
        if tap_handler is None:
            self.__tap = TapPlus(url="http://hst04.n1data.lan:8080/tap-server/tap/")
        else:
            self.__tap = tap_handler

    def get_product(self, observation_id, calibration_level="RAW",
                    filename=None, verbose=False):
        """ Download products from EHST

            Parameters
            ----------
            observation_id : string, id of the observation to be downloaded,
            mandatory
            The identifier of the observation we want to retrieve, regardless
            of whether it is simple or composite.
            calibration_level : string, calibration level, optional, default
            'RAW'
            The identifier of the data reduction/processing applied to the
            data. By default, the most scientifically relevant level will be
            chosen. RAW, CALIBRATED, PRODUCT or AUXILIARY
            filename : string, file name to be used to store the artifact,
            optional, default None
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
            artifact_id : string, id of the artifact to be downloaded,
            mandatory
            The identifier of the physical product (file) we want to retrieve.
            filename : string, file name to be used to store the artifact,
            optional, default None
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

    def get_postcard(self, observation_id, calibration_level="RAW",
                     resolution=256, filename=None, verbose=False):
        """ Download postcards from EHST

            Parameters
            ----------
            observation_id : string, id of the observation for which download
            the postcard, mandatory
            The identifier of the observation we want to retrieve, regardless
            of whether it is simple or composite.
            calibration_level : string, calibration level, optional, default
            'RAW'
            The identifier of the data reduction/processing applied to the
            data. By default, the most scientifically relevant level will be
            chosen. RAW, CALIBRATED, PRODUCT or AUXILIARY
            resolution : integer, postcard resolution, optional, default 256
            Resolution of the retrieved postcard. 256 or 1024
            filename : string, file name to be used to store the postcard,
            optional, default None
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
        link = "".join((self.data_url,
                        retri_type,
                        "&",
                        obs_id,
                        "&",
                        cal_level,
                        "&",
                        res))
        if filename is None:
            filename = observation_id + ".tar"
        print(link)
        return self.__handler.get_file(link, filename, verbose)

    def get_metadata(self, params, filename=None, verbose=False):
        """ It executes a query over EHST and download the xml with the results

            Parameters
            ----------
            params : string, set of restrictions to be applied during the
            execution of the query, mandatory
            Set of restrictions to be applied during the execution of the
            query.
            calibration_level : string, calibration level, optional, default
            'RAW'
            The identifier of the data reduction/processing applied to the
            data. By default, the most scientifically relevant level will be
            chosen. RAW, CALIBRATED, PRODUCT or AUXILIARY
            resolution : integer, postcard resolution, optional, default 256
            Resolution of the retrieved postcard. 256 or 1024
            filename : string, file name to be used to store the postcard,
            optional, default None
            File name for the artifact
            verbose : bool, optional, default 'False'
            Flag to display information about the process

            Returns
            -------
            None. It downloads metadata as a result of the restrictions
            defined.
        """

        link = self.metadata_url + params
        if filename is None:
            filename = "metadata.xml"
        print(link)
        return self.__handler.get_file(link, filename, verbose)

    def cone_search(self, coordinates, radius=0.0, filename=None,
                    verbose=False):
        coord = self.__getCoordInput(coordinates, "coordinate")
        radiusInDrades = float(radius/60) # Converts to degrees

        raHours, dec = commons.coord_to_radec(coord)
        ra = raHours * 15.0  # Converts to degrees
        initial = "".join((
                        "RESOURCE_CLASS=OBSERVATION&SELECTED_FIELDS=",
                        "OBSERVATION&QUERY=(POSITION.RA==",
                        ))
        middle = " AND POSITION.DEC=="
        final = ")&RETURN_TYPE=VOTABLE"
        params = "".join((
                        initial,
                        str(ra),
                        middle,
                        str(dec)+final
                        ))
        params = urllib.request.quote(params)
        link = "".join((
                        self.metadata_url,
                        params
                        ))
        if filename is None:
            filename = "region.xml"
        print(link)
        return self.__handler.get_file(link, filename, verbose)

    def query_target(self, name, filename=None, verbose=False):
        """ It executes a query over EHST and download the xml with the results

            Parameters
            ----------
            name : string, target name to be requested, mandatory
            Target name to be requested.
            filename : string, file name to be used to store the metadata,
            optional, default None
            File name for the artifact
            verbose : bool, optional, default 'False'
            Flag to display information about the process

            Returns
            -------
            None. It downloads metadata as a result of the restrictions
            defined.
        """

        initial = ("RESOURCE_CLASS=OBSERVATION&SELECTED_FIELDS=OBSERVATION"
                   "&QUERY=(TARGET.TARGET_NAME=='")
        final = "')&RETURN_TYPE=VOTABLE"
        link = self.metadata_url + initial + name + final
        if filename is None:
            filename = "target.xml"
        print(link)
        return self.__handler.get_file(link, filename, verbose)

    def query_hst_tap(self, query, output_file=None, 
                       output_format="votable", verbose=False):
        """Launches a synchronous job to query the HST tap

        Parameters
        ----------
        query : str, mandatory
            query (adql) to be executed
        output_file : str, optional, default None
            file name where the results are saved if dumpToFile is True.
            If this parameter is not provided, the jobid is used instead
        output_format : str, optional, default 'votable'
            results format
        verbose : bool, optional, default 'False'
            flag to display information about the process

        Returns
        -------
        A Job object
        """

        return self.__tap.launch_job(query=query, output_file=output_file, 
                              output_format=output_format, verbose=False, dump_to_file=output_file is not None)
    
    def __checkQuantityInput(self, value, msg):
        if not (isinstance(value, str) or isinstance(value, units.Quantity)):
            raise ValueError(
                             str(msg) +
                             " must be either a string or astropy.coordinates")

    def __getQuantityInput(self, value, msg):
        if value is None:
            raise ValueError("Missing required argument: '"+str(msg)+"'")
        if not (isinstance(value, str) or isinstance(value, units.Quantity)):
            raise ValueError(
                             str(msg) +
                             " must be either a string or astropy.coordinates")
        if isinstance(value, str):
            q = Quantity(value)
            return q
        else:
            return value

    def __checkCoordInput(self, value, msg):
        if not (isinstance(value, str) or isinstance(value,
                                                     commons.CoordClasses)):
            raise ValueError(
                             str(msg) +
                             " must be either a string or astropy.coordinates")

    def __getCoordInput(self, value, msg):
        if not (isinstance(value, str) or isinstance(value,
                                                     commons.CoordClasses)):
            raise ValueError(
                             str(msg) +
                             " must be either a string or astropy.coordinates")
        if isinstance(value, str):
            c = commons.parse_coordinates(value)
            return c
        else:
            return value

Hst = HstClass()
