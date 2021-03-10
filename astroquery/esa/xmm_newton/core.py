# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""

@author: Elena Colomo
@contact: ecolomo@esa.int

European Space Astronomy Centre (ESAC)
European Space Agency (ESA)

Created on 3 Sept 2019


"""
import re
from ...utils.tap.core import TapPlus
from ...query import BaseQuery
import shutil
import cgi
from pathlib import Path
import tarfile
import os

from . import conf
from astroquery import log
from astropy.coordinates import SkyCoord


__all__ = ['XMMNewton', 'XMMNewtonClass']


class XMMNewtonClass(BaseQuery):

    data_url = conf.DATA_ACTION
    data_aio_url = conf.DATA_ACTION_AIO
    metadata_url = conf.METADATA_ACTION
    TIMEOUT = conf.TIMEOUT

    def __init__(self, tap_handler=None):
        super(XMMNewtonClass, self).__init__()

        if tap_handler is None:
            self._tap = TapPlus(url="http://nxsa.esac.esa.int"
                                    "/tap-server/tap/")
        else:
            self._tap = tap_handler

    def download_data(self, observation_id, *, filename=None, verbose=False,
                      **kwargs):
        """
        Download data from XMM-Newton

        Parameters
        ----------
        observation_id : string
            id of the observation to be downloaded, mandatory
            The identifier of the observation we want to retrieve, 10 digits
            example: 0144090201
        filename : string
            file name to be used to store the file
        verbose : bool
            optional, default 'False'
            flag to display information about the process
        level : string
            level to download, optional, by default everything is downloaded
            values: ODF, PPS
        instname : string
            instrument name, optional, two characters, by default everything
            values: OM, R1, R2, M1, M2, PN
        instmode : string
            instrument mode, optional
            examples: Fast, FlatFieldLow, Image, PrimeFullWindow
        filter : string
            filter, optional
            examples: Closed, Open, Thick, UVM2, UVW1, UVW2, V
        expflag : string
            exposure flag, optional, by default everything
            values: S, U, X(not applicable)
        expno : integer
            exposure number with 3 digits, by default all exposures
            examples: 001, 003
        name : string
            product type, optional, 6 characters, by default all product types
            examples: 3COLIM, ATTTSR, EVENLI, SBSPEC, EXPMAP, SRCARF
        datasubsetno : character
            data subset number, optional, by default all
            examples: 0, 1
        sourceno : hex value
            source number, optional, by default all sources
            example: 00A, 021, 001
        extension : string
            file format, optional, by default all formats
            values: ASC, ASZ, FTZ, HTM, IND, PDF, PNG


        Returns
        -------
        None if not verbose. It downloads the observation indicated
        If verbose returns the filename
        """

        link = self.data_aio_url + "obsno=" + observation_id

        link = link + "".join("&{0}={1}".format(key, val)
                              for key, val in kwargs.items())

        if verbose:
            log.info(link)

        response = self._request('GET', link, save=False, cache=True)

        # Get original extension
        _, params = cgi.parse_header(response.headers['Content-Disposition'])
        r_filename = params["filename"]
        suffixes = Path(r_filename).suffixes

        if filename is None:
            filename = observation_id

        filename += "".join(suffixes)

        log.info("Copying file to {0}...".format(filename))
        with open(filename, 'wb') as f:
            f.write(response.content)

        if verbose:
            log.info("Wrote {0} to {1}".format(link, filename))

    def get_postcard(self, observation_id, *, image_type="OBS_EPIC",
                     filename=None, verbose=False):
        """
        Download postcards from XSA

        Parameters
        ----------
        observation_id : string
            id of the observation for which download the postcard, mandatory
            The identifier of the observation we want to retrieve, regardless
            of whether it is simple or composite.
        image_type : string
            image type, optional, default 'OBS_EPIC'
            The image_type to be returned. It can be: OBS_EPIC,
            OBS_RGS_FLUXED, OBS_RGS_FLUXED_2, OBS_RGS_FLUXED_3, OBS_EPIC_MT,
            OBS_RGS_FLUXED_MT, OBS_OM_V, OBS_OM_B, OBS_OM_U, OBS_OM_L,
            OBS_OM_M, OBS_OM_S, OBS_OM_W
        filename : string
            file name to be used to store the postcard, optional, default None
        verbose : bool
            optional, default 'False'
            Flag to display information about the process

        Returns
        -------
        None. It downloads the observation postcard indicated
        """

        params = {'RETRIEVAL_TYPE': 'POSTCARD',
                  'OBSERVATION_ID': observation_id,
                  'OBS_IMAGE_TYPE': image_type,
                  'PROTOCOL': 'HTTP'}

        link = self.data_url + "".join("&{0}={1}".format(key, val)
                                       for key, val in params.items())

        if verbose:
            log.info(link)

        local_filepath = self._request('GET', link, params, cache=True, save=True)

        if filename is None:
            response = self._request('HEAD', link)
            response.raise_for_status()
            filename = re.findall('filename="(.+)"', response.headers[
                "Content-Disposition"])[0]
        else:
            filename = observation_id + ".png"

        log.info("Copying file to {0}...".format(filename))

        shutil.move(local_filepath, filename)

        if verbose:
            log.info("Wrote {0} to {1}".format(link, filename))

        return filename

    def query_xsa_tap(self, query, *, output_file=None,
                      output_format="votable", verbose=False):
        """Launches a synchronous job to query the XSA tap

        Parameters
        ----------
        query : str, mandatory
            query (adql) to be executed
        output_file : str, optional, default None
            file name where the results are saved if dumpToFile is True.
            If this parameter is not provided, the jobid is used instead
        output_format : str, optional, default 'votable'
            possible values 'votable' or 'csv'
        verbose : bool, optional, default 'False'
            flag to display information about the process

        Returns
        -------
        A table object
        """

        job = self._tap.launch_job(query=query, output_file=output_file,
                                   output_format=output_format,
                                   verbose=verbose,
                                   dump_to_file=output_file is not None)
        table = job.get_results()
        return table

    def get_tables(self, *, only_names=True, verbose=False):
        """Get the available table in XSA TAP service

        Parameters
        ----------
        only_names : bool, TAP+ only, optional, default 'True'
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
        if only_names:
            return [t.name for t in tables]
        else:
            return tables

    def get_columns(self, table_name, *, only_names=True, verbose=False):
        """Get the available columns for a table in XSA TAP service

        Parameters
        ----------
        table_name : string, mandatory, default None
            table name of which, columns will be returned
        only_names : bool, TAP+ only, optional, default 'True'
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
        for table in tables:
            if str(table.name) == str(table_name):
                columns = table.columns
                break

        if columns is None:
            raise ValueError("table name specified is not found in "
                             "XSA TAP service")

        if only_names:
            return [c.name for c in columns]
        else:
            return columns

    def _parse_filename(self, filename):
        """Parses the file's name of a product

        Parses the file's name of a product following
        http://xmm-tools.cosmos.esa.int/external/xmm_user_support/documentation/dfhb/pps.html

        Parameters
        ----------
        filename : string, mandatory
            The name of the file to be parsed

        Returns
        -------
        A dictionary with field (as specified in the link above)
        as key and the value of each field
        """
        ret = {}
        ret["X"] = filename[0]
        ret["obsidentif"] = filename[1:11]
        ret["I"] = filename[11:13]
        ret["U"] = filename[13]
        ret["E"] = filename[14:17]
        ret["T"] = filename[17:23]
        ret["S"] = filename[23]
        ret["X-"] = filename[24:27]
        ret["Z"] = filename[28:]
        return ret

    def get_epic_images(self, filename, *, band=[], instrument=[],
                        get_detmask=False, get_exposure_map=False, path=""):
        """Extracts the European Photon Imaging Camera (EPIC) images from a given TAR file

        For a given TAR file obtained with:
            XMM.download_data(OBS_ID,level="PPS",extension="FTZ",filename=tarfile)

        This function extracts the EPIC images in a given band (or bands) and
        instrument (or instruments) from it

        The result is a dictionary containing the paths to the extracted EPIC
        images with keys being the band and the instrument

        If the band or the instrument are not specified this function will
        return all the available bands and instruments

        Additionally, ``get_detmask`` and ``get_exposure_map`` can be set to True.
        If so, this function will also extract the exposure maps and detector
        masks within the specified bands and instruments

        Examples
        --------

        Extract all bands and instruments::
            result = XMM.get_epic_images(tarfile,band=[1,2,3,4,5,8],
                                         instrument=['M1','M2','PN'],**kwargs)

        If we want to retrieve the band 3 for the instrument PN (p-n junction)::
            fits_image = result[3]['PN']

        ``fits_image`` will be the full path to the extracted FTZ file

        Extract the exposure and detector maps::
            result = XMM.get_epic_images(tarfile,band=[1,2,3,4,5,8],
                                         instrument=['M1','M2','PN'],
                                         get_detmask=True,
                                         get_exposure_map=True)

        If we want to retrieve exposure map in the band 3 for the instrument PN::
            fits_image = result[3]['PN_expo']

        For retrieving the detector mask in the band 3 for the instrument PN::
            fits_image = result[3]['PN_det']

        Parameters
        ----------
        filename : string, mandatory
            The name of the tarfile to be proccessed
        band : array of integers, optional, default []
            An array of intergers indicating the desired bands
        instruments : array of strings, optional, default []
            An array of strings indicating the desired instruments
        get_detmask : bool, optional
            If True, also extracts the detector masks
        get_exposure_map : bool, optional
            If True, also extracts the exposure maps
        path: string, optional
            If set, extracts the EPIC images in the indicated path

        Returns
        -------
        A dictionary of dictionaries with the full paths of the extracted
        EPIC images. The keys of each dictionary are the band for the first
        level dictionary and the instrument for the second level dictionaries

        Notes
        -----
        The structure and the content of the extracted compressed FITS files
        are described in details in the Pipeline Products Description
        [XMM-SOC-GEN-ICD-0024](https://xmm-tools.cosmos.esa.int/external/xmm_obs_info/odf/data/docs/XMM-SOC-GEN-ICD-0024.pdf).
        """

        _product_type = ["IMAGE_"]
        _instrument = ["M1", "M2", "PN", "EP"]
        _band = [1, 2, 3, 4, 5, 8]
        _path = ""
        if get_detmask:
            _product_type.append("DETMSK")
        if get_exposure_map:
            _product_type.append("EXPMAP")
        if path != "" and os.path.exists(path):
            _path = path

        ret = {}
        if band == []:
            band = _band
        else:
            for i in band:
                if i not in _band:
                    log.warning("Invalid band %u" % i)
                    band.remove(i)

        if instrument == []:
            instrument = _instrument
        else:
            for i in instrument:
                if i not in _instrument:
                    log.warning("Invalid instrument %s" % i)
                    instrument.remove(i)
        with tarfile.open(filename, "r") as tar:
            for member in tar.getmembers():
                paths = os.path.split(member.name)
                fname = paths[1]
                paths = os.path.split(paths[0])
                if paths[1] != "pps":
                    continue
                fname_info = self._parse_filename(fname)
                if fname_info["X"] != "P":
                    continue
                if not fname_info["I"] in instrument:
                    continue
                if not int(fname_info["S"]) in band:
                    continue
                if not fname_info["T"] in _product_type:
                    continue
                tar.extract(member, _path)
                if not ret.get(int(fname_info["S"])):
                    ret[int(fname_info["S"])] = {}
                b = int(fname_info["S"])
                ins = fname_info["I"]
                value = os.path.abspath(os.path.join(_path, member.name))
                if fname_info["T"] == "DETMSK":
                    ins = fname_info["I"] + "_det"
                elif fname_info["T"] == "EXPMAP":
                    ins = fname_info["I"] + "_expo"
                if ret[b].get(ins) and type(ret[b].get(ins)) == str:
                    log.warning("More than one file found with the "
                                "band %u and "
                                "the instrument: %s" % (b, ins))
                    ret[b][ins] = [ret[b][ins], value]
                elif ret[b].get(ins) and type(ret[b].get(ins)) == list:
                    ret[b][ins].append(value)
                else:
                    ret[b][ins] = value

        return ret

    def get_epic_metadata(self, *, target_name=None,
                          coordinates=None, radius=None):
        """Downloads the European Photon Imaging Camera (EPIC)
        metadata from a given target

        Parameters
        ----------
        target_name : string, optional, default None
            The name of the target
        coordinates : `~astropy.coordinates.SkyCoord`, optinal, default None
            The coordinates of the target in a SkyCoord object
        radius : float, optional, default None
            The radius to query the target in degrees

        Returns
        -------
        epic_source,  cat_4xmm, stack_4xmm, slew_source : `~astropy.table.Table` objects
            Tables containing the metadata of the target
        """
        if not target_name and not coordinates:
                raise Exception("Input parameters needed, "
                                "please provide the name "
                                "or the coordinates of the target")

        epic_source = {"table": "xsa.v_epic_source",
                       "column": "epic_source_equatorial_spoint"}
        cat_4xmm = {"table": "xsa.v_epic_source_cat",
                    "column": "epic_source_cat_equatorial_spoint"}
        stack_4xmm = {"table": "xsa.v_epic_xmm_stack_cat",
                      "column": "epic_stack_cat_equatorial_spoint"}
        slew_source = {"table": "xsa.v_slew_source_cat",
                       "column": "slew_source_cat_equatorial_spoint"}

        cols = "*"

        c = coordinates
        if not coordinates:
            c = SkyCoord.from_name(target_name, parse=True)

        if type(c) is not SkyCoord:
            raise Exception("The coordinates must be an "
                            "astroquery.coordinates.SkyCoord object")
        if not radius:
            radius = 0.1

        query_fmt = ("select {} from {} "
                     "where 1=contains({}, circle('ICRS', {}, {}, {}));")
        epic_source_table = self.query_xsa_tap(query_fmt.format(cols,
                                               epic_source["table"],
                                               epic_source["column"],
                                               c.ra.degree,
                                               c.dec.degree,
                                               radius))
        cat_4xmm_table = self.query_xsa_tap(query_fmt.format(cols,
                                            cat_4xmm["table"],
                                            cat_4xmm["column"],
                                            c.ra.degree,
                                            c.dec.degree,
                                            radius))
        stack_4xmm_table = self.query_xsa_tap(query_fmt.format(cols,
                                              stack_4xmm["table"],
                                              stack_4xmm["column"],
                                              c.ra.degree,
                                              c.dec.degree,
                                              radius))
        slew_source_table = self.query_xsa_tap(query_fmt.format(cols,
                                               slew_source["table"],
                                               slew_source["column"],
                                               c.ra.degree,
                                               c.dec.degree,
                                               radius))
        return epic_source_table, cat_4xmm_table, stack_4xmm_table, slew_source_table


XMMNewton = XMMNewtonClass()
