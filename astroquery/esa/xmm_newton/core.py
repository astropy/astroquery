# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
============================
XMM-Newton Astroquery Module
============================

European Space Astronomy Centre (ESAC)
European Space Agency (ESA)

"""
import re
import shutil
from pathlib import Path
import tarfile as esatar
import os
import configparser
from email.message import Message

from astropy.io import fits
from astroquery import log
from astropy.coordinates import SkyCoord

from . import conf
from ...exceptions import LoginError
from ...utils.tap.core import TapPlus
from ...query import BaseQuery, QueryWithLogin


__all__ = ['XMMNewton', 'XMMNewtonClass']


# We do trust the ESA tar files, this is to avoid the new to Python 3.12 deprecation warning
# https://docs.python.org/3.12/library/tarfile.html#tarfile-extraction-filter
if hasattr(esatar, "fully_trusted_filter"):
    esatar.TarFile.extraction_filter = staticmethod(esatar.fully_trusted_filter)


class XMMNewtonClass(BaseQuery):
    data_url = conf.DATA_ACTION
    data_aio_url = conf.DATA_ACTION_AIO
    metadata_url = conf.METADATA_ACTION
    TIMEOUT = conf.TIMEOUT

    def __init__(self, tap_handler=None):
        super().__init__()
        self.configuration = configparser.ConfigParser()

        if tap_handler is None:
            self._tap = TapPlus(url="https://nxsa.esac.esa.int/tap-server/tap")
        else:
            self._tap = tap_handler
        self._rmf_ftp = str("http://sasdev-xmm.esac.esa.int/pub/ccf/constituents/extras/responses/")

    def download_data(self, observation_id, *, filename=None, verbose=False,
                      cache=True, prop=False, credentials_file=None, **kwargs):
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
        prop: boolean
            optional, default 'False'
            flag to download proprietary data, the method will then ask the user to
            input their username and password either manually or using the credentials_file
        credentials_file: string
            optional, default None
            path to where the users config.ini file is stored with their username and password
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
        cache : bool
            Defaults to True. If set overrides global caching behavior.
            See :ref:`caching documentation <astroquery_cache>`.

        Returns
        -------
        None if not verbose. It downloads the observation indicated
        If verbose returns the filename
        """

        # create url to access the aio
        link = self._create_link(observation_id, **kwargs)

        # If the user wants to access proprietary data, ask them for their credentials
        if prop:
            username, password = self._get_username_and_password(credentials_file)
            link = f"{link}&AIOUSER={username}&AIOPWD={password}"

        if verbose:
            log.info(link)

        # get response of created url
        params = self._request_link(link, cache)
        r_filename = params["filename"]
        suffixes = Path(r_filename).suffixes

        # get desired filename
        filename = self._create_filename(filename, observation_id, suffixes)
        """
        If prop we change the log level so that it is above 20, this is to stop a log.debug (line 431) in query.py.
        This debug reveals the url being sent which in turn reveals the users username and password
        """
        if prop:
            previouslevel = log.getEffectiveLevel()
            log.setLevel(21)
            self._download_file(link, filename, head_safe=True, cache=cache)
            log.setLevel(previouslevel)
        else:
            self._download_file(link, filename, head_safe=True, cache=cache)

        if verbose:
            log.info(f"Wrote {link} to {filename}")

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
            filename = os.path.basename(re.findall('filename="(.+)"', response.headers[
                "Content-Disposition"])[0])
        else:
            filename = observation_id + ".png"

        log.info(f"Copying file to {filename}...")

        shutil.move(local_filepath, filename)

        if verbose:
            log.info(f"Wrote {link} to {filename}")

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
            raise ValueError("table name specified is not found in XSA TAP service")

        if only_names:
            return [c.name for c in columns]
        else:
            return columns

    def _create_link(self, observation_id, **kwargs):
        link = f"{self.data_aio_url}obsno={observation_id}"
        link = link + "".join("&{0}={1}".format(key, val)
                              for key, val in kwargs.items())
        return link

    def _request_link(self, link, cache):
        # we can cache this HEAD request - the _download_file one will check
        # the file size and will never cache
        response = self._request('HEAD', link, save=False, cache=cache)
        # Get original extension
        if 'Content-Type' in response.headers and 'text' not in response.headers['Content-Type']:
            message = Message()
            message["content-type"] = response.headers["Content-Disposition"]
            params = dict(message.get_params()[1:])
        elif response.status_code == 401:
            error = "Data protected by proprietary rights. Please check your credentials"
            raise LoginError(error)
        elif 'Content-Type' not in response.headers:
            error = "Incorrect credentials"
            raise LoginError(error)
        response.raise_for_status()
        return params

    def _get_username_and_password(self, credentials_file):
        if credentials_file is not None:
            self.configuration.read(credentials_file)
            xmm_username = self.configuration.get("xmm_newton", "username")
            password = self.configuration.get("xmm_newton", "password")
        else:
            xmm_username = input("Username: ")
            password, password_from_keyring = QueryWithLogin._get_password(self, service_name="xmm_newton",
                                                                           username=xmm_username, reenter=False)
        return xmm_username, password

    def _create_filename(self, filename, observation_id, suffixes):
        if filename is not None:
            filename = os.path.basename(os.path.splitext(filename)[0])
        else:
            filename = observation_id
        filename += "".join(suffixes)
        return filename

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

    def get_epic_spectra(self, filename, source_number, *,
                         instrument=[], path="", verbose=False):
        """Extracts in path (when set) the EPIC sources spectral products from a
        given TAR file.

        This function extracts the EPIC sources spectral products in a given
        instrument (or instruments) from it
        The result is a dictionary containing the paths to the extracted EPIC
        sources spectral products with key being the instrument
        If the instrument is not specified this function will
        return all the available instruments

        Parameters
        ----------
        filename : string, mandatory
            The name of the tarfile to be processed
        source_number : integer, mandatory
            The source number, in decimal, in the observation
        instruments : array of strings, optional, default []
            An array of strings indicating the desired instruments
        path: string, optional
            If set, extracts the EPIC images in the indicated path
        verbose : bool
            optional, default 'False'
            flag to display information about the process

        Returns
        -------
        A dictionary with the full paths of the extracted EPIC sources
        spectral products. The key is the instrument

        Notes
        -----
        The filenames will contain the source number in hexadecimal,
        as this is the convention used by the pipeline.
        The structure and the content of the extracted compressed FITS files
        are described in details in the Pipeline Products Description
        [XMM-SOC-GEN-ICD-0024]
        (https://xmm-tools.cosmos.esa.int/external/xmm_obs_info/odf/data/docs/XMM-SOC-GEN-ICD-0024.pdf).

        The RMF to be used for the spectral analysis should be generated with the same PPS version as the spectrum,
        background and ARF. The PPS version can be found in SASVERS keyword in the SPECTRUM file, characters [-6:-3].
        Once the sas version is determined, the code should look for the proper version of RMF in the FTP tree.
        However, for the current PPS versions available in the archive, i.e v18.0, v19.0, v20.0 and v21.0,
        all RMF matrices are equal among the versions and for all instruments, so it is possible to download the last
        one, v21.0, available in the root FTP stored in 'rmf_ftp'. In the future, the FTP tree and/or PPS keywords will
        be modified to make it easier to download the appropriate RMF file for each spectrum.
        """
        _instrument = ["M1", "M2", "PN", "EP"]
        _product_type = ["SRSPEC", "BGSPEC", "SRCARF"]
        _path = ""
        ret = None
        if instrument == []:
            instrument = _instrument
        else:
            for inst in instrument:
                if inst not in _instrument:
                    log.warning(f"Invalid instrument {inst}")
                    instrument.remove(inst)
        if path != "" and os.path.exists(path):
            _path = path
        try:
            with esatar.open(filename, "r") as tar:
                ret = {}
                for member in [x for x in tar.getmembers() if not x.name.lower().endswith('png')]:
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
                    if not fname_info["T"] in _product_type:
                        continue
                    if int(fname_info["X-"], 16) != source_number:
                        continue
                    tar.extract(member, _path)
                    key = fname_info["I"]
                    path_inst_name = os.path.abspath(os.path.join(_path, member.name))
                    if fname_info["T"] == "BGSPEC":
                        key = fname_info["I"] + "_bkg"
                    elif fname_info["T"] == "SRCARF":
                        key = fname_info["I"] + "_arf"
                    else:
                        with fits.open(path_inst_name) as hdul:
                            for ext in hdul:
                                if ext.name != "SPECTRUM":
                                    continue
                                rmf_fname = ext.header["RESPFILE"]
                                if fname_info["I"] == "M1" or fname_info["I"] == "M2":
                                    inst = "MOS/" + str(ext.header["SPECDELT"]) + "eV/"
                                elif fname_info["I"] == "PN":
                                    inst = "PN/"
                                    file_name, file_ext = os.path.splitext(rmf_fname)
                                    rmf_fname = file_name + "_v21.0" + file_ext

                                link = self._rmf_ftp + inst + rmf_fname

                                if verbose:
                                    log.info("rmf link is: %s" % link)

                                response = self._request('GET', link)

                                rsp_filename = os.path.join(_path, paths[0], paths[1], ext.header["RESPFILE"])

                                with open(rsp_filename, 'wb') as f:
                                    f.write(response.content)
                                    ret[fname_info["I"] + "_rmf"] = rsp_filename

                    if ret.get(key) and type(ret.get(key)) == str:
                        log.warning("More than one file found with the instrument: %s" % key)
                        ret[key] = [ret[key], path_inst_name]
                    elif ret.get(key) and type(ret.get(key)) == list:
                        ret[key].append(path_inst_name)
                    else:
                        ret[key] = path_inst_name

        except FileNotFoundError:
            log.error("File %s not found" % (filename))
            return

        if not ret:
            log.info("Nothing to extract with the given parameters:\n"
                     "  PPS: %s\n"
                     "  Source Number: %u\n"
                     "  Instrument: %s\n" % (filename, source_number,
                                             instrument))

        return ret

    def get_epic_images(self, filename, band=[], instrument=[],
                        get_detmask=False, get_exposure_map=False, path="", **kwargs):

        """Extracts the EPIC images from a given TAR file

        This function extracts the EPIC images in a given band (or bands) and
        instrument (or instruments) from it

        The result is a dictionary containing the paths to the extracted EPIC
        images with keys being the band and the instrument

        If the band or the instrument are not specified this function will
        return all the available bands and instruments

        Additionally, ``get_detmask`` and ``get_exposure_map`` can be set to True.
        If so, this function will also extract the exposure maps and detector
        masks within the specified bands and instruments

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

        ret = None
        if band == []:
            band = _band
        else:
            for b in band:
                if b not in _band:
                    log.warning("Invalid band %u" % b)
                    band.remove(b)

        if instrument == []:
            instrument = _instrument
        else:
            for inst in instrument:
                if inst not in _instrument:
                    log.warning("Invalid instrument %s" % inst)
                    instrument.remove(inst)
        try:
            with esatar.open(filename, "r") as tar:
                ret = {}
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
                    path_member_name = os.path.abspath(os.path.join(_path, member.name))
                    if fname_info["T"] == "DETMSK":
                        ins = fname_info["I"] + "_det"
                    elif fname_info["T"] == "EXPMAP":
                        ins = fname_info["I"] + "_expo"
                    if ret[b].get(ins) and type(ret[b].get(ins)) == str:
                        log.warning("More than one file found with the "
                                    "band %u and "
                                    "the instrument: %s" % (b, ins))
                        ret[b][ins] = [ret[b][ins], path_member_name]
                    elif ret[b].get(ins) and type(ret[b].get(ins)) == list:
                        ret[b][ins].append(path_member_name)
                    else:
                        ret[b][ins] = path_member_name

        except FileNotFoundError:
            log.error("File %s not found" % (filename))
            return None

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
            raise ValueError("Input parameters needed, "
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
            raise TypeError("The coordinates must be an "
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

    def get_epic_lightcurve(self, filename, source_number, *,
                            instrument=[], path=""):
        """Extracts the EPIC sources light curve products from a given TAR file

        For a given TAR file obtained with ``XMMNewton.download_data``.

        This function extracts the EPIC sources light curve products in a given
        instrument (or instruments) from said TAR file

        The result is a dictionary containing the paths to the extracted EPIC
        sources light curve products with the key being the instrument

        If the instrument is not specified, this function will
        return all available instruments

        Parameters
        ----------
        filename : string, mandatory
            The name of the tarfile to be proccessed
        source_number : integer, mandatory
            The source number, in decimal, in the observation
        instruments : array of strings, optional, default []
            An array of strings indicating the desired instruments
        path: string, optional
            If set, extracts the EPIC images in the indicated path

        Returns
        -------
        A dictionary with the full paths of the extracted EPIC sources
        light curve products. The key is the instrument

        Notes
        -----
        The filenames will contain the source number in hexadecimal,
        as this is the convention used by the pipeline.

        The structure and the content of the extracted compressed FITS files
        are described in details in the Pipeline Products Description
        [XMM-SOC-GEN-ICD-0024](https://xmm-tools.cosmos.esa.int/external/xmm_obs_info/odf/data/docs/XMM-SOC-GEN-ICD-0024.pdf).

        """
        _instrumnet = ["M1", "M2", "PN", "EP"]
        _band = [8]
        _product_type = ["SRCTSR", "FBKTSR"]
        _path = ""

        ret = None

        if instrument == []:
            instrument = _instrumnet
        else:
            for inst in instrument:
                if inst not in _instrumnet:
                    log.warning("Invalid instrument %s" % inst)
                    instrument.remove(inst)

        if path != "" and os.path.exists(path):
            _path = path

        try:
            with esatar.open(filename, "r") as tar:
                ret = {}
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
                    if not int(fname_info["S"]) in _band:
                        continue
                    if not fname_info["T"] in _product_type:
                        continue
                    if int(fname_info["X-"], 16) != source_number:
                        continue
                    tar.extract(member, _path)
                    key = fname_info["I"]
                    path_inst_name = os.path.abspath(os.path.join(_path, member.name))
                    if fname_info["T"] == "FBKTSR":
                        key = fname_info["I"] + "_bkg"
                    if ret.get(key) and type(ret.get(key)) == str:
                        log.warning("More than one file found with the "
                                    "instrument: %s" % key)
                        ret[key] = [ret[key], path_inst_name]
                    elif ret.get(key) and type(ret.get(key)) == list:
                        ret[key].append(path_inst_name)
                    else:
                        ret[key] = path_inst_name

        except FileNotFoundError:
            log.error("File %s not found" % (filename))
            return None

        if ret is None or ret == {}:
            log.info("Nothing to extract with the given parameters:\n"
                     "  PPS: %s\n"
                     "  Source Number: %u\n"
                     "  Instrument: %s\n" % (filename, source_number,
                                             instrument))

        return ret


XMMNewton = XMMNewtonClass()
