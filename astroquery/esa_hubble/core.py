# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""

@author: Javier Duran
@contact: javier.duran@sciops.esa.int

European Space Astronomy Centre (ESAC)
European Space Agency (ESA)

Created on 13 Aug. 2018


"""
from astroquery.utils import commons
from astropy import units
from astropy.units import Quantity
from astroquery.utils.tap.core import TapPlus
from astroquery.utils.tap.model import modelutils
from astroquery.query import BaseQuery
from astropy.table import Table
from six import BytesIO
import os

from . import conf
from astropy import log


__all__ = ['EsaHubble', 'EsaHubbleClass']


class ESAHubbleHandler(BaseQuery):

    def __init__(self):
        super(ESAHubbleHandler, self).__init__()

    def get_file(self, filename, response, verbose=False):
        with open(filename, 'wb') as fh:
            fh.write(response.content)

        if os.pathsep not in filename:
            log.info("File {0} downloaded to current "
                     "directory".format(filename))
        else:
            log.info("File {0} downloaded".format(filename))

    def get_table(self, filename, response, output_format='votable',
                  verbose=False):
        with open(filename, 'wb') as fh:
            fh.write(response.content)

        table = modelutils.read_results_table_from_file(filename,
                                                        str(output_format))
        return table

    def request(self, t="GET", link=None, params=None,
                cache=None,
                timeout=None):
        return self._request(method=t, url=link,
                             params=params, cache=cache,
                             timeout=timeout)


Handler = ESAHubbleHandler()


class ESAHubbleClass(BaseQuery):

    data_url = conf.DATA_ACTION
    metadata_url = conf.METADATA_ACTION
    TIMEOUT = conf.TIMEOUT

    def __init__(self, url_handler=None, tap_handler=None):
        super(ESAHubbleClass, self).__init__()
        if url_handler is None:
            self._handler = Handler
        else:
            self._handler = url_handler

        if tap_handler is None:
            self._tap = TapPlus(url="http://hst.esac.esa.int"
                                    "/tap-server/tap/")
        else:
            self._tap = tap_handler

    def download_product(self, observation_id, calibration_level="RAW",
                         filename=None, verbose=False):
        """
        Download products from EHST

        Parameters
        ----------
        observation_id : string
            id of the observation to be downloaded, mandatory
            The identifier of the observation we want to retrieve, regardless
            of whether it is simple or composite.
        calibration_level : string
            calibration level, optional, default 'RAW'
            The identifier of the data reduction/processing applied to the
            data. By default, the most scientifically relevant level will be
            chosen. RAW, CALIBRATED, PRODUCT or AUXILIARY
        filename : string
            file name to be used to store the artifact, optional, default
            None
            File name for the observation.
        verbose : bool
            optional, default 'False'
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

        response = self._handler.request('GET', link)
        if response is not None:
            response.raise_for_status()
            self._handler.get_file(filename, response=response,
                                   verbose=verbose)

            if verbose:
                log.info("Wrote {0} to {1}".format(link, filename))
            return filename

    def get_artifact(self, artifact_id, filename=None, verbose=False):
        """
        Download artifacts from EHST. Artifact is a single Hubble product file.

        Parameters
        ----------
        artifact_id : string
            id of the artifact to be downloaded, mandatory
            The identifier of the physical product (file) we want to retrieve.
        filename : string
            file name to be used to store the artifact, optional, default None
            File name for the artifact
        verbose : bool
            optional, default 'False'
            flag to display information about the process

        Returns
        -------
        None. It downloads the artifact indicated
        """

        art_id = "ARTIFACT_ID=" + artifact_id
        link = self.data_url + art_id
        result = self._handler.request('GET', link, params=None)
        if verbose:
            log.info(link)
        if filename is None:
            filename = artifact_id
        self._handler.get_file(filename, response=result, verbose=verbose)

    def get_postcard(self, observation_id, calibration_level="RAW",
                     resolution=256, filename=None, verbose=False):
        """
        Download postcards from EHST

        Parameters
        ----------
        observation_id : string
            id of the observation for which download the postcard, mandatory
            The identifier of the observation we want to retrieve, regardless
            of whether it is simple or composite.
        calibration_level : string
            calibration level, optional, default 'RAW'
            The identifier of the data reduction/processing applied to the
            data. By default, the most scientifically relevant level will be
            chosen. RAW, CALIBRATED, PRODUCT or AUXILIARY
        resolution : integer
            postcard resolution, optional, default 256
            Resolution of the retrieved postcard. 256 or 1024
        filename : string
            file name to be used to store the postcard, optional, default None
            File name for the artifact
        verbose : bool
            optional, default 'False'
            Flag to display information about the process

        Returns
        -------
        None. It downloads the observation postcard indicated
        """

        retri_type = "RETRIEVAL_TYPE=POSTCARD"
        obs_id = "OBSERVATION_ID=" + observation_id
        cal_level = "CALIBRATION_LEVEL=" + calibration_level
        res = "RESOLUTION=" + str(resolution)
        link = self.data_url + "&".join([retri_type, obs_id, cal_level, res])

        result = self._handler.request('GET', link, params=None)
        if verbose:
            log.info(link)
        if filename is None:
            filename = observation_id + ".tar"
        self._handler.get_file(filename, response=result, verbose=verbose)

    def cone_search(self, coordinates, radius=0.0, filename=None,
                    output_format='votable', cache=True):
        """
        """
        coord = self._getCoordInput(coordinates, "coordinate")
        radiusInGrades = float(radius/60)  # Converts to degrees

        raHours, dec = commons.coord_to_radec(coord)
        ra = raHours * 15.0  # Converts to degrees
        payload = {"RESOURCE_CLASS": "OBSERVATION",
                   "ADQLQUERY": "SELECT DISTINCT OBSERVATION,OBSERVATION.TYPE,"
                   "TARGET.MOVING_TARGET"
                   ",TARGET.TARGET_NAME,TARGET.TARGET_DESCRIPTION,PROPOSAL."
                   "PROPOSAL_ID,PROPOSAL.PI_"
                   "NAME,PROPOSAL.PROPOSAL_TITLE,INSTRUMENT.INSTRUMENT_NAME,"
                   "PLANE.METADATA_PROVENANCE"
                   ",PLANE.DATA_PRODUCT_TYPE,PLANE.SOFTWARE_VERSION,POSITION"
                   ".RA,POSITION.DEC,POSITION."
                   "GAL_LAT,POSITION.GAL_LON,POSITION.ECL_LAT,POSITION.ECL_LON"
                   ",POSITION.FOV_SIZE,ENERGY."
                   "WAVE_CENTRAL,ENERGY.WAVE_BANDWIDTH,ENERGY.WAVE_MAX,ENERGY"
                   ".WAVE_MIN,ENERGY.FILTER FROM"
                   " FIELD_NOT_USED  WHERE OBSERVATION.COLLECTION='HST'  AND  "
                   "PLANE.MAIN_SCIENCE_PLANE="
                   "'true'  AND  (OBSERVATION.TYPE='HST Composite' OR "
                   "OBSERVATION.TYPE='HST Singleton')"
                   "  AND  INTERSECTS(CIRCLE('ICRS', {0}, {1}, {2}"
                   "),POSITION)=1  AND  PLANE.MAIN_SCIENCE_PLANE='true' "
                   "ORDER BY PROPOSAL.PROPOSAL_ID "
                   "DESC".format(str(ra), str(dec), str(radiusInGrades)),
                   "RETURN_TYPE": str(output_format)}
        result = self._handler.request('GET',
                                       self.metadata_url,
                                       params=payload,
                                       cache=cache,
                                       timeout=self.TIMEOUT)
        if filename is None:
            filename = "cone." + str(output_format)

        if result is None:
            table = None
        else:
            fileobj = BytesIO(result.content)
            table = Table.read(fileobj, format=output_format)
            # TODO: add "correct units" material here

        return table

    def query_target(self, name, filename=None, output_format='votable',
                     verbose=False):
        """
        It executes a query over EHST and download the xml with the results.

        Parameters
        ----------
        name : string
            target name to be requested, mandatory
        filename : string
            file name to be used to store the metadata, optional, default None
        output_format : string
            optional, default 'votable'
            output format of the query
        verbose : bool
            optional, default 'False'
            Flag to display information about the process

        Returns
        -------
        Table with the result of the query. It downloads metadata as a file.
        """

        initial = ("RESOURCE_CLASS=OBSERVATION&SELECTED_FIELDS=OBSERVATION"
                   "&QUERY=(TARGET.TARGET_NAME=='")
        final = "')&RETURN_TYPE=" + str(output_format)
        link = self.metadata_url + initial + name + final
        result = self._handler.request('GET', link, params=None)
        if verbose:
            log.info(link)
        if filename is None:
            filename = "target.xml"
        return self._handler.get_table(filename,
                                       response=result,
                                       output_format=output_format,
                                       verbose=verbose)

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
        A table object
        """

        job = self._tap.launch_job(query=query, output_file=output_file,
                                   output_format=output_format,
                                   verbose=False,
                                   dump_to_file=output_file is not None)
        table = job.get_results()
        return table

    def get_tables(self, only_names=True, verbose=False):
        """Get the available table in EHST TAP service

        Parameters
        ----------
        only_names : bool, TAP+ only, optional, default 'False'
            True to load table names only
        verbose : bool, optional, default 'False'
            flag to display information about the process

        Returns
        -------
        A list of tables
        """

        tables = self._tap.load_tables(only_names=only_names,
                                       include_shared_tables=False,
                                       verbose=verbose)
        if only_names is True:
            table_names = []
            for t in tables:
                table_names.append(t.name)
            return table_names
        else:
            return tables

    def get_columns(self, table_name, only_names=True, verbose=False):
        """Get the available columns for a table in EHST TAP service

        Parameters
        ----------
        table_name : string, mandatory, default None
            table name of which, columns will be returned
        only_names : bool, TAP+ only, optional, default 'False'
            True to load table names only
        verbose : bool, optional, default 'False'
            flag to display information about the process

        Returns
        -------
        A list of columns
        """

        tables = self._tap.load_tables(only_names=False,
                                       include_shared_tables=False,
                                       verbose=verbose)
        columns = None
        for t in tables:
            if str(t.name) == str(table_name):
                columns = t.columns
                break

        if columns is None:
            raise ValueError("table name specified is not found in "
                             "EHST TAP service")

        if only_names is True:
            column_names = []
            for c in columns:
                column_names.append(c.name)
            return column_names
        else:
            return columns

    def _checkQuantityInput(self, value, msg):
        if not (isinstance(value, str) or isinstance(value, units.Quantity)):
            raise ValueError(str(msg) + ""
                             " must be either a string or astropy.coordinates")

    def _getQuantityInput(self, value, msg):
        if value is None:
            raise ValueError("Missing required argument: '"+str(msg)+"'")
        if not (isinstance(value, str) or isinstance(value, units.Quantity)):
            raise ValueError(str(msg) + ""
                             " must be either a string or astropy.coordinates")
        if isinstance(value, str):
            q = Quantity(value)
            return q
        else:
            return value

    def _checkCoordInput(self, value, msg):
        if not (isinstance(value, str) or isinstance(value,
                                                     commons.CoordClasses)):
            raise ValueError(str(msg) + ""
                             " must be either a string or astropy.coordinates")

    def _getCoordInput(self, value, msg):
        if not (isinstance(value, str) or isinstance(value,
                                                     commons.CoordClasses)):
            raise ValueError(str(msg) + ""
                             " must be either a string or astropy.coordinates")
        if isinstance(value, str):
            c = commons.parse_coordinates(value)
            return c
        else:
            return value


ESAHubble = ESAHubbleClass()
