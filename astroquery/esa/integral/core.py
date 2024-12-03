# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
======================
ISLA Astroquery Module
======================

European Space Astronomy Centre (ESAC)
European Space Agency (ESA)

"""
import numpy as np
from astropy.units import Quantity
from astropy.table import Table
from astroquery.query import BaseQuery, BaseVOQuery
from astroquery import log
import getpass
import pyvo
from . import conf
import time
from ..utils.utils import download_table, ESAAuthSession, get_coord_input, get_degree_radius, execute_servlet_request, \
    plot_result, plot_concatenated_results, plot_image, download_file
from datetime import datetime

__all__ = ['Integral', 'IntegralClass']


class IntegralClass(BaseVOQuery, BaseQuery):
    """
    Class to init ESA Integral Module and communicate with isla
    """

    TIMEOUT = conf.TIMEOUT

    def __init__(self, tap_handler=None, auth_session=None):

        # Checks if auth session has been defined. If not, create a new session
        if auth_session:
            self._auth_session = auth_session
        else:
            self._auth_session = ESAAuthSession()

        if tap_handler is None:
            self.tap = pyvo.dal.TAPService(
                conf.ISLA_TAP_SERVER, session=self._auth_session)
        else:
            self.tap = tap_handler
            self._data = None

        self.instrument_band_map = self.__get_instrument_band_map()

    def query_tap(self, query, *, async_job=False, output_file=None, output_format=None):
        """Launches a synchronous or asynchronous job to query the ISLA tap

        Parameters
        ----------
        query : str, mandatory
            query (adql) to be executed
        async_job : bool, optional, default 'False'
            executes the query (job) in asynchronous/synchronous mode (default
            synchronous)
        output_file : str, optional, default None
            file name where the results are saved if dumpToFile is True.
            If this parameter is not provided, the jobid is used instead
        output_format : str, optional, default 'votable'
            results format

        Returns
        -------
        An astropy.table object containing the results
        """
        if async_job:
            job = self.tap.submit_job(query)
            job.run()
            while job.phase == 'EXECUTING':
                time.sleep(3)
            result = job.fetch_result().to_table()
        else:
            result = self.tap.search(query).to_table()

        if output_file:
            download_table(result, output_file, output_format)

        return result

    def get_sources(self, target_name, *, async_job=False, output_file=None, output_format=None):
        """Retrieve the coordinates of an INTEGRAL source

        Parameters
        ----------
        target_name : str, mandatory
            target name to be requested, mandatory
        async_job : bool, optional, default 'False'
            executes the query (job) in asynchronous/synchronous mode (default
            synchronous)
        output_file : str, optional, default None
            file name where the results are saved if dumpToFile is True.
            If this parameter is not provided, the jobid is used instead
        output_format : str, optional, default 'votable'
            results format

        Returns
        -------
        An astropy.table object containing the results
        """

        query = conf.ISLA_TARGET_CONDITION.format(target_name)
        result = self.query_tap(query=query, async_job=async_job, output_file=output_file, output_format=output_format)

        if len(result) > 0:
            return result

        raise ValueError(f"Target {target_name} cannot be resolved for ISLA")

    def get_observations(self, *, target_name=None, coordinates=None, radius=14.0, start_time=None, end_time=None,
                         start_revno=None, end_revno=None, async_job=False, output_file=None, output_format=None,
                         verbose=False):
        """Retrieve the INTEGRAL observations associated to target name, time range and/or revolution

        Parameters
        ----------
        target_name: str, optional
            target name to be requested
        coordinates: str or SkyCoord, optional
            coordinates of the center in the cone search
        radius: float or quantity, optional, default value 14 degrees
            radius in degrees (int, float) or quantity of the cone_search
        start_time: str in UTC or datetime, optional
            start time of the observation
        end_time: str in UTC or datetime, optional
            end time of the observation
        start_revno: string, optional
            start revolution number, as a four-digit string with leading zeros
        end_revno: string, optional
            end revolution number, as a four-digit string with leading zeros
        async_job : bool, optional, default 'False'
            executes the query (job) in asynchronous/synchronous mode (default
            synchronous)
        output_file : str, optional, default None
            file name where the results are saved if dumpToFile is True.
            If this parameter is not provided, the jobid is used instead
        output_format : str, optional, default 'votable'
            results format
        verbose : bool, optional, default 'False'
            flag to display information about the process

        Returns
        -------
        An astropy.table object containing the results
        """
        base_query = conf.ISLA_OBSERVATION_BASE_QUERY
        query = base_query
        conditions = []

        # Target name/Coordinates + radius condition
        if target_name and coordinates:
            raise TypeError("Please use only target or coordinates as "
                            "parameter.")

        if radius:
            radius = get_degree_radius(radius)

        if target_name:
            coord = self.get_sources(target_name=target_name)
            ra = coord['ra'][0]
            dec = coord['dec'][0]
            conditions.append(conf.ISLA_COORDINATE_CONDITION.format(ra, dec, radius))
        elif coordinates:
            coord = get_coord_input(value=coordinates, msg=coordinates)
            ra = coord.ra.degree
            dec = coord.dec.degree
            conditions.append(conf.ISLA_COORDINATE_CONDITION.format(ra, dec, radius))

        # Start/End time conditions
        if start_time:
            parsed_start = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            conditions.append(f"endtime >= '{parsed_start}'")

        if end_time:
            parsed_end = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            conditions.append(f"starttime <= '{parsed_end}'")

        # Revolution Number conditions
        if start_revno and self.__validate_revno(start_revno):
            conditions.append(f"end_revno >= '{start_revno}'")

        if end_revno and self.__validate_revno(end_revno):
            conditions.append(f"start_revno <= '{end_revno}'")

        # Create final query
        if conditions:
            query = f"{query} where {' AND '.join(conditions)}"

        query = f"{query} order by obsid"
        if verbose:
            return query
        else:
            return self.query_tap(query=query, async_job=async_job, output_file=output_file,
                                  output_format=output_format)

    def download_science_windows(self, *, science_windows=None, observation_id=None, revolution=None, proposal=None,
                                 output_file=None):
        """Method to download science windows associated to one of these parameters:
        science_windows, observation_id, revolution or proposal

        Parameters
        ----------
        science_windows : list of str, optional
            Science Windows to download
        observation_id: str, optional
            Observation ID associated to science windows
        revolution: str, optional
            Revolution associated to science windows
        proposal: str, optional
            Proposal ID associated to science windows
        output_file: str, optional
            File name and path for the downloaded file

        Returns
        -------
        The path and filename of the file with science windows
        """

        params = self.__get_science_window_parameter(science_windows, observation_id, revolution, proposal)
        params['RETRIEVAL_TYPE'] = 'SCW'
        params['TAPCLIENT'] = 'ASTROQUERY'

        return download_file(url=conf.ISLA_DATA_SERVER, session=self._auth_session, filename=output_file, params=params,
                             verbose=True)

    def get_timeline(self, ra, dec, *, radius=14, plot=False, plot_revno=False, plot_distance=False):
        """Retrieve the INTEGRAL timeline associated to coordinates and radius

        Parameters
        ----------
        ra: float, mandatory
            Right ascension
        dec: float, mandatory
            Declination
        radius: float or quantity, optional, default value 14 degrees
            radius in degrees (int, float) or quantity of the cone_search
        plot: boolean, optional, default value False
            show the timeline using matplotlib
        plot_revno: boolean, optional, default value False
            If plot is True, show in the X-Axis the revolution number
            instead of the date
        plot_distance: boolean, optional, default value False
            If plot is True, show in the distance plot concatenated to the timeline

        Returns
        -------
        An object containing:
            totalItems: a counter for the number of items retrieved
            fraFC:
            totEffExpo:
            timeline: An astropy.table object containing the results for scwExpo, scwRevs, scwTimes and scwOffAxis
        """

        if radius:
            radius = get_degree_radius(radius)

        query_params = {
            'REQUEST': 'timelines',
            "ra": ra,
            "dec": dec,
            "radius": radius,
            "TAPCLIENT": 'ASTROQUERY'
        }

        request_result = execute_servlet_request(url=conf.ISLA_SERVLET,
                                                 tap=self.tap,
                                                 query_params=query_params)
        total_items = request_result['totalItems']
        data = request_result['data']
        fraFC = data['fraFC']
        totEffExpo = data['totEffExpo']
        timeline = Table({
            "scwExpo": data["scwExpo"],
            "scwRevs": data["scwRevs"],
            "scwTimes": [datetime.fromtimestamp(scwTime / 1000) for scwTime in data["scwTimes"]],
            "scwOffAxis": data["scwOffAxis"]
        })

        if plot:
            x = timeline['scwRevs'] if plot_revno else timeline['scwTimes']
            x_label = 'Revolutions' if plot_revno else 'Calendar Dates'
            if plot_distance:
                plot_concatenated_results(x, timeline['scwExpo'] / 1000, timeline['scwOffAxis'],
                                          x_label, 'Effective Exposure (ks)', 'Distance (deg)',
                                          'Observations', x_label='Pointing (Ks)',
                                          y_label='Off-axis (deg)')
            else:
                plot_result(x, timeline['scwExpo'] / 1000,
                            x_label, 'Effective Exposure (ks)',
                            'Observations')

        return {'total_items': total_items, 'fraFC': fraFC, 'totEffExpo': totEffExpo, 'timeline': timeline}

    def get_epochs(self, target_name, *, instrument=None, band=None):
        """Retrieve the INTEGRAL epochs associated to a target and an instrument or a band

        Parameters
        ----------
        target_name : str, mandatory
            target name to be requested, mandatory
        instrument : str, optional
            Possible values: jem-x, ibis
        band : str, optional
            Possible values: 03_20, 28_40

        Returns
        -------
        An astropy.table object containing the available epochs
        """

        value = self.__get_instrument_or_band(instrument=instrument, band=band)
        instrument_oid, band_oid = self.__get_oids(value)

        query = conf.ISLA_EPOCH_QUERY.format(target_name, instrument_oid, band_oid)
        return self.query_tap(query)

    def get_long_term_timeseries(self, target_name, *, instrument=None, band=None, plot=False):
        """Retrieve the INTEGRAL long term timeseries associated to the target and instrument pr bamd

        Parameters
        ----------
        target_name : str, mandatory
            target name to be requested, mandatory
        instrument : str, optional
            Possible values: jem-x, ibis
        band : str, optional
            Possible values: 03_20, 28_40
        plot: boolean
            show the long term timeseries using matplotlib

        Returns
        -------
        An object containing:
            source_id: id of the source
            aggregation_value
            total_items: total number of elements in the timeseries
            aggregation_unit
            detectors: a list of the detector available for that instrument
            timeseries_list: A list of astropy.table object containing the long term timeseries
        """

        value = self.__get_instrument_or_band(instrument=instrument, band=band)

        query_params = {
            'REQUEST': 'long_timeseries',
            "source": target_name,
            "instrument_oid": self.instrument_band_map[value]['instrument_oid'],
            "TAPCLIENT": 'ASTROQUERY'
        }

        request_result = execute_servlet_request(url=conf.ISLA_SERVLET,
                                                 tap=self.tap,
                                                 query_params=query_params)
        source_id = request_result['sourceId']
        aggregation_value = request_result['aggregationValue']
        total_items = request_result['totalItems']
        aggregation_unit = request_result['aggregationUnit']
        detectors = request_result['detectors']
        # Retrieve all the timeseries for each detector
        timeseries_list = []
        for i in range(0, len(detectors)):
            timeseries_list.append(Table({
                "time": [datetime.fromisoformat(timeseries_time) for timeseries_time in request_result["time"][i]],
                "rates": request_result["rates"][i],
                "ratesError": request_result["ratesError"][i],
            }))

        if plot:
            for i, timeseries in enumerate(timeseries_list):
                plot_result(timeseries['time'], timeseries['rates'],
                            'Time', 'Rate (cps)',
                            f"Long Term Timeseries ({detectors[i]})", error_y=timeseries['ratesError'])

        return {'source_id': source_id, 'aggregation_value': aggregation_value,
                'total_items': total_items, 'aggregation_unit': aggregation_unit,
                'detectors': detectors, 'timeseries_list': timeseries_list}

    def download_long_term_timeseries(self, target_name, *, instrument=None, band=None, output_file=None):
        """Method to download long term timeseries associated to an epoch and instrument or band

        Parameters
        ----------
        target_name : str, mandatory
            target name to be requested, mandatory
        instrument : str
            Possible values: jem-x, ibis
        band : str
            Possible values: 03_20, 28_40

        output_file: str, optional
            File name and path for the downloaded file

        Returns
        -------
        The path and filename of the file with long term timeseries
        """

        value = self.__get_instrument_or_band(instrument=instrument, band=band)

        params = {'RETRIEVAL_TYPE': 'long_timeseries',
                  'source': target_name,
                  "instrument_oid": self.instrument_band_map[value]['instrument_oid'],
                  'TAPCLIENT': 'ASTROQUERY'}
        return download_file(url=conf.ISLA_DATA_SERVER, session=self._auth_session, filename=output_file,
                             params=params, verbose=True)

    def get_short_term_timeseries(self, target_name, epoch, instrument=None, band=None, *, plot=False):
        """Retrieve the INTEGRAL short term timeseries associated to the target and instrument or band

        Parameters
        ----------
        target_name : str, mandatory
            target name to be requested, mandatory
        epoch : str, mandatory
            reference epoch for the short term timeseries
        instrument : str, optional
            Possible values: jem-x, ibis
        band : str, optional
            Possible values: 03_20, 28_40
        plot: boolean, optional
            show the long term timeseries using matplotlib

        Returns
        -------
        An object containing:
            source_id: id of the source
            total_items: total number of elements in the timeseries
            detectors: a list of the detector available for that instrument
            timeseries_list: A list of astropy.table object containing the short term timeseries
        """

        value = self.__get_instrument_or_band(instrument=instrument, band=band)

        query_params = {
            'REQUEST': 'short_timeseries',
            "source": target_name,
            "band_oid": self.instrument_band_map[value]['band_oid'],
            "epoch": epoch,
            "TAPCLIENT": 'ASTROQUERY'
        }

        request_result = execute_servlet_request(url=conf.ISLA_SERVLET,
                                                 tap=self.tap,
                                                 query_params=query_params)
        source_id = request_result['sourceId']
        total_items = request_result['totalItems']
        detectors = request_result['detectors']
        # Retrieve all the timeseries for each detector
        timeseries_list = []
        for i in range(0, len(detectors)):
            timeseries_list.append(Table({
                "time": [datetime.fromisoformat(timeseries_time) for timeseries_time in request_result["time"][i]],
                "rates": request_result["rates"][i],
                "rates_error": request_result["ratesError"][i],
            }))

        if plot:
            for i, timeseries in enumerate(timeseries_list):
                plot_result(timeseries['time'], timeseries['rates'],
                            'Time', 'Rate (cps)',
                            f"Light curve ({detectors[i]})", error_y=timeseries['rates_error'])

        return {'source_id': source_id, 'total_items': total_items, 'detectors': detectors,
                'timeseries_list': timeseries_list}

    def download_short_term_timeseries(self, target_name, epoch, *, instrument=None, band=None, output_file=None):
        """Method to download short term timeseries associated to an epoch and instrument or band

        Parameters
        ----------
        target_name : str, mandatory
            target name to be requested, mandatory
        epoch : str, mandatory
            reference epoch for the short term timeseries
        instrument : str, optional
            Possible values: jem-x, ibis
        band : str, optional
            Possible values: 03_20, 28_40
        output_file: str, optional
            File name and path for the downloaded file

        Returns
        -------
        The path and filename of the file with short term timeseries

        """

        value = self.__get_instrument_or_band(instrument=instrument, band=band)

        params = {'RETRIEVAL_TYPE': 'short_timeseries',
                  'source': target_name,
                  'band_oid': self.instrument_band_map[value]['band_oid'],
                  'epoch': epoch,
                  'TAPCLIENT': 'ASTROQUERY'}
        return download_file(url=conf.ISLA_DATA_SERVER, session=self._auth_session, filename=output_file, params=params,
                             verbose=True)

    def get_spectra(self, target_name, epoch, instrument=None, band=None, *, plot=False):
        """Retrieve the INTEGRAL spectra associated to the target and instrument or band

        Parameters
        ----------
        target_name : str, mandatory
            target name to be requested, mandatory
        instrument : str, optional
            Possible values: jem-x, ibis
        band : str, optional
            Possible values: 03_20, 28_40
        epoch : str, mandatory
            reference epoch for the short term timeseries
        plot: boolean, optional
            show the long term timeseries using matplotlib

        Returns
        -------
        spectrum: a list of objects containing the parameters of the spectra and
            an astropy.table object containing the spectra
        """

        value = self.__get_instrument_or_band(instrument=instrument, band=band)

        query_params = {
            'REQUEST': 'spectra',
            "source": target_name,
            "instrument_oid": self.instrument_band_map[value]['instrument_oid'],
            "epoch": epoch,
            "TAPCLIENT": 'ASTROQUERY'
        }

        request_result = execute_servlet_request(url=conf.ISLA_SERVLET,
                                                 tap=self.tap,
                                                 query_params=query_params)
        spectrum = []
        for element in request_result:
            spectra_element = {}

            spectra_element['spectra_oid'] = element['spectraOid']
            spectra_element['file_name'] = element['fileName']
            spectra_element['metadata'] = element['metadata']
            spectra_element['date_start'] = element['dateStart']
            spectra_element['date_stop'] = element['dateStop']
            spectra_element['detector'] = element['detector']
            # Retrieve all the timeseries for each detector
            spectra_element['spectra'] = Table({"energy": element['energy'],
                                                "energy_error": element["energyError"],
                                                'rate': element["rate"],
                                                "rate_error": element["rateError"],
                                                })

            spectrum.append(spectra_element)
            if plot:
                plot_result(spectra_element['spectra']['energy'], spectra_element['spectra']['rate'],
                            'Energy (keV)', 'Counts s⁻¹ keV⁻¹',
                            f"Spectrum", error_x=spectra_element['spectra']['energy_error'],
                            error_y=spectra_element['spectra']['rate_error'], log_scale=True)

        return spectrum

    def download_spectra(self, target_name, epoch, *, instrument=None, band=None, output_file=None):
        """Method to download mosaics associated to an epoch and instrument or band

        Parameters
        ----------
        target_name : str, mandatory
            target name to be requested, mandatory
        epoch : str, mandatory
            reference epoch for the short term timeseries
        instrument : str
            Possible values: jem-x, ibis
        band : str
            Possible values: 03_20, 28_40
        output_file: str, optional
            File name and path for the downloaded file

        Returns
        -------
        A list of paths and filenames of the files with spectras
        """

        spectrum = self.get_spectra(target_name=target_name, epoch=epoch, instrument=instrument, band=band, plot=False)
        downloaded_files = []
        for spectra in spectrum:
            params = {'RETRIEVAL_TYPE': 'spectras',
                      'spectra_oid': spectra['spectra_oid'],
                      'TAPCLIENT': 'ASTROQUERY'}
            downloaded_files.append(
                download_file(url=conf.ISLA_DATA_SERVER, session=self._auth_session, filename=output_file,
                              params=params,
                              verbose=True))
        return downloaded_files

    def get_mosaic(self, epoch, instrument=None, band=None, *, plot=False):
        """Retrieve the INTEGRAL mosaics associated to the instrument or band

        Parameters
        ----------
        epoch : str, mandatory
            reference epoch for the short term timeseries
        instrument : str, optional
            Possible values: jem-x, ibis
        band : str, optional
            Possible values: 03_20, 28_40

        plot: boolean, optional
            show the long term timeseries using matplotlib

        Returns
        -------
        mosaics: a list of objects containing the parameters of the mosaic and
            an astropy.table object containing the mosaic
        """

        value = self.__get_instrument_or_band(instrument=instrument, band=band)

        query_params = {
            'REQUEST': 'mosaics',
            "band_oid": self.instrument_band_map[value]['band_oid'],
            "epoch": epoch,
            "TAPCLIENT": 'ASTROQUERY'
        }

        request_result = execute_servlet_request(url=conf.ISLA_SERVLET,
                                                 tap=self.tap,
                                                 query_params=query_params)
        mosaics = []
        for element in request_result:
            mosaic_element = {}

            mosaic_element['file_name'] = element['fileName']
            mosaic_element['mosaic_oid'] = element['mosaicOid']
            mosaic_element['height'] = element['height']
            mosaic_element['width'] = element['width']
            mosaic_element['min_z_scale'] = element['minZScale']
            mosaic_element['max_z_scale'] = element['maxZScale']
            # Retrieve all the timeseries for each detector
            mosaic_element['mosaic'] = Table({
                'ra': np.array(element['ra'], dtype=float).flatten().flatten(),
                'dec': np.array(element['dec'], dtype=float).flatten().flatten(),
                'data': np.array(element['data'], dtype=float).flatten().flatten()
            })

            mosaics.append(mosaic_element)
            if plot:
                plot_image(mosaic_element['mosaic']['data'], 'Mosaic',
                           mosaic_element['height'], mosaic_element['width'])

        return mosaics

    def download_mosaic(self, epoch, *, instrument=None, band=None, output_file=None):
        """Method to download mosaics associated to an epoch and instrument or band

        Parameters
        ----------
        epoch : str, mandatory
            reference epoch for the short term timeseries
        instrument : str
            Possible values: jem-x, ibis
        band : str
            Possible values: 03_20, 28_40

        output_file: str, optional
            File name and path for the downloaded file

        Returns
        -------
        A list of paths and filenames of the files with mosaics
        """

        mosaics = self.get_mosaic(epoch=epoch, instrument=instrument, band=band, plot=False)
        downloaded_files = []
        for mosaic in mosaics:
            params = {'RETRIEVAL_TYPE': 'mosaics',
                      'mosaic_oid': mosaic['mosaic_oid'],
                      'TAPCLIENT': 'ASTROQUERY'}
            downloaded_files.append(
                download_file(url=conf.ISLA_DATA_SERVER, session=self._auth_session, filename=output_file,
                              params=params,
                              verbose=True))
        return downloaded_files

    def get_source_metadata(self, target_name):
        """Retrieve the metadata associated to an INTEGRAL target

        Parameters
        ----------
        target_name : str, mandatory
            target name to be requested, mandatory

        Returns
        -------
        An object containing te metadata from the target
        """
        query_params = {
            'REQUEST': 'sources',
            "SOURCE": target_name,
            "TAPCLIENT": 'ASTROQUERY'
        }
        return execute_servlet_request(url=conf.ISLA_SERVLET,
                                       tap=self.tap,
                                       query_params=query_params)

    def __get_instrument_band_map(self):
        """
        Maps the bands and instruments included in ISLA
        """
        instrument_band_table = self.query_tap(conf.ISLA_INSTRUMENT_BAND_QUERY)
        instrument_band_map = {}

        for row in instrument_band_table:
            instrument_band_map[row['instrument']] = {'band': row['band'],
                                                      'instrument_oid': row['instrument_oid'],
                                                      'band_oid': row['band_oid']}
            instrument_band_map[row['band']] = {'instrument': row['instrument'],
                                                'instrument_oid': row['instrument_oid'],
                                                'band_oid': row['band_oid']}

        return instrument_band_map

    def __get_instrument_or_band(self, instrument, band):
        if instrument and band:
            raise TypeError("Please use only instrument or band as "
                            "parameter.")

        if instrument is None and band is None:
            raise TypeError("Please use at least one parameter, instrument or band.")

        if instrument:
            return instrument
        else:
            return band

    def __get_oids(self, value):
        """
        Retrieves the band_oid and instrument_oid associated to a band or instrument
        Parameters
        ----------
        value: str
            value to check
        """

        return self.instrument_band_map[value]['instrument_oid'], self.instrument_band_map[value]['band_oid']

    def __validate_revno(self, rev_no):
        """
        Verifies if the format for revolution number is correct
         Parameters
        ----------
        rev_no: str
            revolution number
        """
        if len(rev_no) == 4:
            return True
        raise ValueError(f"Revolution number {rev_no} is not correct. It must be a four-digit number as a string, "
                         f"with leading zeros to complete the four digits")

    def __get_science_window_parameter(self, science_windows, observation_id, revolution, proposal):
        """
        Verifies if only one parameter is not null and return its value
         Parameters
        ----------
        science_windows : list of str, mandat
            Science Windows to download
        observation_id: str, optional
            Observation ID associated to science windows
        revolution: str, optional
            Revolution associated to science windows
        proposal: str, optional
            Proposal ID associated to science windows

        Returns
        -------
        The correct parameter for the science windows
        """
        params = [science_windows, observation_id, revolution, proposal]

        # Count how many are not None
        non_none_count = sum(p is not None for p in params)

        # Ensure only one parameter is provided
        if non_none_count > 1:
            raise ValueError("Only one parameter can be provided at a time.")

        if science_windows is not None:
            if isinstance(science_windows, str):
                return {'scwid': science_windows}
            elif isinstance(science_windows, list):
                return {'scwid': ','.join(science_windows)}

        if observation_id is not None:
            return {'obsid': observation_id}

        if revolution is not None:
            return {'REVID': revolution}

        if proposal is not None:
            return {'PROPID': proposal}


Integral = IntegralClass()
