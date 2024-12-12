import io
import re
import tarfile
import warnings

from bs4 import BeautifulSoup

from astropy.io import votable, fits
from astropy.table import Table

from astroquery.query import BaseQuery
from astroquery.utils import class_or_instance
from astroquery.exceptions import InvalidQueryError, NoResultsWarning

from . import conf


__all__ = ["Most", "MostClass"]


class MostClass(BaseQuery):
    URL = conf.most_server
    TIMEOUT = conf.timeout

    def _validate_name_input_type(self, params):
        """
        Validate required parameters when ``input_type='name_input'``.

        Parameters
        ----------
        params : `dict`
            Dictionary of query parameters to validate.

        Raises
        ------
        ValueError
            If the input does not have the minimum required parameters set to
            an at least truthy value.
        """
        if not params.get("obj_name", False):
            raise ValueError("When input type is 'name_input' key 'obj_name' is required.")

    def _validate_nafid_input_type(self, params):
        """
        Validate required parameters when ``input_type='naifid_input'``.


        Parameters
        ----------
        params : `dict`
            Dictionary of query parameters to validate.

        Raises
        ------
        ValueError
            If the input does not have the minimum required parameters set to
            an at least truthy value.
        """
        if not params.get("obj_nafid", False):
            raise ValueError("When input type is 'nafid_input' key 'obj_nafid' is required.")

    def _validate_mpc_input_type(self, params):
        """
        Validate required parameters when ``input_type='mpc_input'``.

        Parameters
        ----------
        params : `dict`
            Dictionary of query parameters to validate.

        Raises
        ------
        ValueError
            If the input does not have the minimum required parameters set to
            an at least truthy value.
        """
        obj_type = params.get("obj_type", False)
        if not obj_type:
            raise ValueError("When input type is 'mpc_input' key 'obj_type' is required.")
        if obj_type not in ("Asteroid", "Comet"):
            raise ValueError("Object type is case sensitive and must be one of: `Asteroid` or `Comet`")

        if not params.get("mpc_data", False):
            raise ValueError("When input type is 'mpc_input' key 'mpc_data' is required.")

    def _validate_manual_input_type(self, params):
        """
        Validate required parameters when ``input_type='manual_input'``.

        Parameters
        ----------
        params : `dict`
            Dictionary of query parameters to validate.

        Raises
        ------
        ValueError
            If the input does not have the minimum required parameters set to
            an at least truthy value.
        """
        obj_type = params.get("obj_type", False)
        if not obj_type:
            raise ValueError("When input type is 'manual_input' key 'obj_type' is required.")
        if obj_type not in ("Asteroid", "Comet"):
            raise ValueError("Object type is case sensitive and must be one of: 'Asteroid' or 'Comet'")

        # MOST will always require at least the distance and eccentricity
        # distance param is named differently in cases of asteroids and comets
        if not params.get("eccentricity", False):
            raise ValueError("When input_type is 'manual_input', 'eccentricity' is required.")

        if obj_type == "Asteroid":
            if not params.get("semimajor_axis", False):
                raise ValueError("When obj_type is 'Asteroid', 'semimajor_axis' is required.")
        elif obj_type == "Comet":
            if not params.get("perih_dist", False):
                raise ValueError("When obj_type is 'Comet', 'perih_dist' is required.")

        # This seemingly can be whatever
        if not params.get("body_designation", False):
            params["body_designation"] = "Test"+params["obj_type"]

    def _validate_input(self, params):
        """
        Validate the minimum required set of parameters, for a given input
        type, are at least truthy.

        These include the keys ``catalog``, ``input_type``, ``output_mode`` and
        ``ephem_step`` in addition to keys required by the specified input type.

        Parameters
        ----------
        params : `dict`
            Dictionary of query parameters to validate.

        Raises
        ------
        ValueError
            If the input does not have the minimum required parameters set to
            an at least truthy value.
        """
        if params.get("catalog", None) is None:
            raise ValueError("Which catalog is being queried is always required.")

        input_type = params.get("input_type", None)
        if input_type is None:
            raise ValueError("Input type is always required.")

        if input_type == "name_input":
            self._validate_name_input_type(params)
        elif input_type == "nafid_input":
            self._validate_nafid_input_type(params)
        elif input_type == "mpc_input":
            self._validate_mpc_input_type(params)
        elif input_type == "manual_input":
            self._validate_manual_input_type(params)
        else:
            raise ValueError(
                "Unrecognized 'input_type'. Expected `name_input`, `nafid_input` "
                f"`mpc_input` or `manual_input`, got {input_type} instead."
            )

    def _parse_full_regular_response(self, response, withTarballs=False):
        """
        Parses the response when output type is set to ``"Regular"`` or ``"Full"``.

        Parameters
        ----------
        response : `requests.models.Response`
            Query response.
        withTarballs : `bool`, optional
            Parse the links to FITS and region tarballs from the response. By
            default, set to False.

        Returns
        -------
        retdict : `dict`
            Dictionary containing the keys ``results``, ``metadata`` and ``region``.
            Optionally can contain keys ``fits_tarball`` and ``region_tarball``.
            The ``results`` and ``metadata`` are an `astropy.table.Table` object
            containing the links to image and region files and minimum object
            metadata, while ``metadata`` contains the image metadata and object
            positions. The ``region`` key contains a link to the DS9 region file
            representing the matched object trajectory and search boxes. When
            existing, ``fits_tarball`` and ``region_tarball`` are links to the
            tarball archives of the fits and region images.
        """
        retdict = {}
        html = BeautifulSoup(response.content, "html5lib")
        download_tags = html.find_all("a", string=re.compile(".*Download.*"))

        # If for some reason this wasn't a full response with downloadable tags,
        # raise an explicit exception:
        if not download_tags:
            raise ValueError('Something has gone wrong, there are no results parsed. '
                             f'For full response see: {response.text}')
        # this is "Download Results Table (above)"
        results_response = self._request("GET", download_tags[0]["href"])
        retdict["results"] = Table.read(results_response.text, format="ipac")

        # this is "Download Image Metadata with Matched Object position Table"
        imgmet_response = self._request("GET", download_tags[1]["href"])
        retdict["metadata"] = Table.read(imgmet_response.text, format="ipac")

        # this is "Download DS9 Region File with the Orbital Path", it's a link
        # to a DS9 region file
        # regions_response = self._request("GET", download_tags[2]["href"])
        retdict["region"] = download_tags[2]["href"]

        if withTarballs:
            retdict["fits_tarball"] = download_tags[-1]["href"]
            retdict["region_tarball"] = download_tags[-2]["href"]

        return retdict

    @class_or_instance
    def list_catalogs(self):
        """Returns a list of queriable catalogs."""
        response = self._request("GET", conf.most_interface_url, timeout=self.TIMEOUT)

        html = BeautifulSoup(response.content, "html5lib")
        catalog_dropdown_options = html.find("select").find_all("option")

        catalogs = [tag.string for tag in catalog_dropdown_options]

        # The Internal-Use-only datasets are free to search in MOST.
        # The way it is supposed to work is that the images will not be accessible.
        if "--- Internal use only:" in catalogs:
            catalogs.remove("--- Internal use only:")
        return catalogs

    def get_images(self, catalog="wise_merge", input_mode="name_input", ephem_step=0.25,
                   obs_begin=None, obs_end=None, obj_name=None, obj_nafid=None, obj_type=None,
                   mpc_data=None, body_designation=None, epoch=None, eccentricity=None,
                   inclination=None, arg_perihelion=None, ascend_node=None, semimajor_axis=None,
                   mean_anomaly=None, perih_dist=None, perih_time=None, get_query_payload=False,
                   save=False, savedir=''):
        """Gets images containing the specified object or orbit.

        Parameters are case sensitive.
        See module help for more details.

        Parameters
        ----------
        catalog : str
            Catalog to query.
            Required.
            Default ``"wise_merge"``.
        input_mode : str
            Input mode. One of ``"name_input"``, ``"naifid_input"``,
            ``"mpc_input"`` or ``"manual_input"``.
            Required.
            Default: ``"name_input"``.
        ephem_step : 0.25,
            Size of the steps (in days) at which the object ephemeris is evaluated.
            Required.
            Default: 0.25
        obs_begin : str or None
            UTC of the start of observations in ``YYYY-MM-DD``. When ``None``
            queries all availible data in the catalog which can be slow.
            Optional.
            Default: ``None``.
        obs_end : str or None
            UTC of the end of observations in ``YYYY-MM-DD``. When ``None``
            queries all availible data in the catalog, can be slow.
            Optional.
            Default: ``None``.
        obj_name : str or None
            Object name.
            Required when input mode is ``"name_input"``.
        obj_nafid : str or None
            Object NAIFD.
            Required when input mode is ``"naifid_input"``.
        obj_type : str or None
            Object type, ``"Asteroid"`` or ``Comet``.
            Required when input mode is ``"mpc_input"`` or ``"manual_input"``.
        mpc_data : str or None
            MPC formatted object string.
            Required when input mode is ``"mpc_input"``.
        body_designation : str or None
            Name of the object described by the given orbital parameters. Does
            not have to be a real name. Will default to ``"TestAsteroid"`` or
            ``"TestComet"`` depending on selected object type.
            Required when input mode is ``"manual_input"``.
        epoch : str or None
            Epoch in MJD.
            Required when input mode is ``"manual_input"``.
        eccentricity : float or None
            Eccentricity (0-1).
            Required when input mode is ``"manual_input"``.
        inclination : float or None
            Inclination (0-180 degrees).
            Required when input mode is ``"manual_input"``.
        arg_perihelion : str or None
            Argument of perihelion (0-360 degrees).
            Required when input mode is ``"manual_input"``.
        ascend_node : float or None
            Longitude of the ascending node (0-360).
            Required when input mode is ``"manual_input"``.
        semimajor_axis : float or None
            Semimajor axis (AU).
            Required when input mode is ``"manual_input"`` and object type is
            ``"Asteroid"``.
        mean_anomaly : str or None
            Mean anomaly (degrees).
            Required when input mode is ``"manual_input"`` and object type is
            ``"Asteroid"``.
        perih_dist : float or None
            Perihelion distance (AU).
            Required when input mode is ``"manual_input"`` and object type is
            ``"Comet"``.
        perih_time : str or None
            Perihelion time (YYYY+MM+DD+HH:MM:SS).
            Required when input mode is ``"manual_input"`` and object type is
            ``"Comet"``.
        get_query_payload : bool
            Return the query parameters as a dictionary. Useful for debugging.
            Optional.
            Default: ``False``
        save : bool
            Whether to save the file to a local directory.
        savedir : str
            The location to save the local file if you want to save it
            somewhere other than `~astroquery.query.BaseQuery.cache_location`

        Returns
        -------
        images : list
            A list of `~astropy.io.fits.HDUList` objects.
        """
        # We insist on output_mode being regular so that it executes quicker,
        # and we insist on tarballs so the download is quicker. We ignore
        # whatever else user provides, but leave the parameters as arguments to
        # keep the same signatures for doc purposes.
        queryres = self.query_object(
            catalog=catalog,
            input_mode=input_mode,
            obs_begin=obs_begin,
            obs_end=obs_end,
            ephem_step=ephem_step,
            obj_name=obj_name,
            obj_nafid=obj_nafid,
            obj_type=obj_type,
            mpc_data=mpc_data,
            body_designation=body_designation,
            epoch=epoch,
            eccentricity=eccentricity,
            inclination=inclination,
            arg_perihelion=arg_perihelion,
            ascend_node=ascend_node,
            semimajor_axis=semimajor_axis,
            mean_anomaly=mean_anomaly,
            perih_dist=perih_dist,
            perih_time=perih_time,
            get_query_payload=get_query_payload,
            output_mode="Regular",
            with_tarballs=True,
        )

        if queryres is None:
            # A warning will already be issued by query_object so no need to
            # raise a new one here.
            return None

        response = self._request("GET", queryres["fits_tarball"],
                                 save=save, savedir=savedir)

        archive = tarfile.open(fileobj=io.BytesIO(response.content))
        images = []
        for name in archive.getnames():
            if ".fits" in name:
                fileobj = archive.extractfile(name)
                fitsfile = fits.open(fileobj)
                images.append(fitsfile)

        return images

    @class_or_instance
    def query_object(self, catalog="wise_merge", input_mode="name_input", output_mode="Regular",
                     ephem_step=0.25, with_tarballs=False, obs_begin=None, obs_end=None,
                     obj_name=None, obj_nafid=None, obj_type=None, mpc_data=None,
                     body_designation=None, epoch=None, eccentricity=None, inclination=None,
                     arg_perihelion=None, ascend_node=None, semimajor_axis=None, mean_anomaly=None,
                     perih_dist=None, perih_time=None, get_query_payload=False):
        """
        Query the MOST interface using specified parameters and/or default
        query values.

        MOST service takes an object/orbit, depending on the input mode,
        evaluates its ephemerides in the, in the given time range, and returns
        a combination of image identifiers, image metadata and/or ephemerides
        depending on the output mode.

        The required and optional query parameters vary depending on the query
        input type. Provided parameters that do not match the given input type
        will be ignored. Certain parameters are always required input to the
        service. For these the provided default values match the defaults of
        the online MOST interface.

        Parameters are case sensitive.
        See module help for more details.

        Parameters
        ----------
        catalog : str
            Catalog to query.
            Required.
            Default ``"wise_merge"``.
        input_mode : str
            Input mode. One of ``"name_input"``, ``"naifid_input"``,
            ``"mpc_input"`` or ``"manual_input"``.
            Required.
            Default: ``"name_input"``.
        output_mode : str
            Output mode. One of ``"Regular"``, ``"Full"``, ``"Brief"``,
            ``"Gator"`` or ``"VOTable"``.
            Required.
            Default: ``"Regular"``
        ephem_step : 0.25,
            Size of the steps (in days) at which the object ephemeris is evaluated.
            Required.
            Default: 0.25
        with_tarballs : bool
            Return links to tarballs of found FITS and Region files.
            Optional, only when output mode is ``"Regular"`` or ``"Full"``.
            Default: ``False``
        obs_begin : str or None
            UTC of the start of observations in ``YYYY-MM-DD``. When ``None``
            queries all availible data in the catalog which can be slow.
            Optional.
            Default: ``"None"``.
        obs_end : str or None
            UTC of the end of observations in ``YYYY-MM-DD``. When ``None``
            queries all availible data in the catalog, can be slow.
            Optional.
            Default: ``None``
        obj_name : str or None
            Object name.
            Required when input mode is ``"name_input"``.
        obj_nafid : str or None
            Object NAIFD
            Required when input mode is ``"naifid_input"``.
        obj_type : str or None
            Object type, ``"Asteroid"`` or ``Comet``
            Required when input mode is ``"mpc_input"`` or ``"manual_input"``.
        mpc_data : str or None
            MPC formatted object string.
            Required when input mode is ``"mpc_input"``.
        body_designation : str or None
            Name of the object described by the given orbital parameters. Does
            not have to be a real name. Will default to ``"TestAsteroid"`` or
            ``"TestComet"`` depending on selected object type.
            Required when input mode is ``"manual_input"``.
        epoch : str or None
            Epoch in MJD.
            Required when input mode is ``"manual_input"``.
        eccentricity : float or None
            Eccentricity (0-1).
            Required when input mode is ``"manual_input"``.
        inclination : float or None
            Inclination (0-180 degrees).
            Required when input mode is ``"manual_input"``.
        arg_perihelion : str or None
            Argument of perihelion (0-360 degrees).
            Required when input mode is ``"manual_input"``.
        ascend_node : float or None
            Longitude of the ascending node (0-360).
            Required when input mode is ``"manual_input"``.
        semimajor_axis : float or None
            Semimajor axis (AU).
            Required when input mode is ``"manual_input"`` and object type is
            ``"Asteroid"``.
        mean_anomaly : str or None
            Mean anomaly (degrees).
            Required when input mode is ``"manual_input"`` and object type is
            ``"Asteroid"``.
        perih_dist : float or None
            Perihelion distance (AU).
            Required when input mode is ``"manual_input"`` and object type is
            ``"Comet"``.
        perih_time : str or None
            Perihelion time (YYYY+MM+DD+HH:MM:SS).
            Required when input mode is ``"manual_input"`` and object type is
            ``"Comet"``.
        get_query_payload : bool
            Return the query parameters as a dictionary. Useful for debugging.
            Optional.
            Default: ``False``

        Returns
        -------
        query_results : `~astropy.table.Table`, `~astropy.io.votable.tree.VOTableFile` or `dict`
            Results of the query. Content depends on the selected output mode.
            In ``"Full"`` or ``"Regular"`` output mode returns a dictionary
            containing at least ``results``, ``metadata`` and ``region`` keys,
            and optionally ``fits_tarball`` and ``region_tarball`` keys. When
            in ``"Brief"`` or ``"Gator"`` an `~astropy.table.Table` object and
            in ``"VOTable"`` an `~astropy.io.votable.tree.VOTableFile`. See
            module help for more details on the content of these tables.
        """
        # This is a map between the keyword names used by the MOST cgi-bin
        # service and their more user-friendly names. For example,
        # input_type -> input_mode or fits_region_files --> with tarballs
        qparams = {
            "catalog": catalog,
            "input_type": input_mode,
            "output_mode": output_mode,
            "obs_begin": obs_begin,
            "obs_end": obs_end,
            "ephem_step": ephem_step,
            "fits_region_files": "on" if with_tarballs else "",
            "obj_name": obj_name,
            "obj_nafid": obj_nafid,
            "obj_type": obj_type,
            "mpc_data": mpc_data,
            "body_designation": body_designation,
            "epoch": epoch,
            "eccentricity": eccentricity,
            "inclination": inclination,
            "arg_perihelion": arg_perihelion,
            "ascend_node": ascend_node,
            "semimajor_axis": semimajor_axis,
            "mean_anomaly": mean_anomaly,
            "perih_dist": perih_dist,
            "perih_time": perih_time,
        }

        if get_query_payload:
            return qparams

        self._validate_input(qparams)
        response = self._request("POST", self.URL,
                                 data=qparams, timeout=self.TIMEOUT)

        # service unreachable or some other reason
        response.raise_for_status()

        # MOST will not raise an bad response if the query is bad because they
        # are not a REST API
        if "MOST: *** error:" in response.text or "most: error:" in response.text:
            raise InvalidQueryError(response.text)

        # presume that response is HTML to simplify conditions
        if "Number of Matched Image Frames   = 0" in response.text:
            warnings.warn("Number of Matched Image Frames   = 0", NoResultsWarning)
            return None

        if qparams["output_mode"] in ("Brief", "Gator"):
            return Table.read(response.text, format="ipac")
        elif qparams["output_mode"] == "VOTable":
            matches = votable.parse(io.BytesIO(response.content))
            if matches.get_table_by_index(0).nrows == 0:
                warnings.warn("Number of Matched Image Frames   = 0", NoResultsWarning)
                return Table()
            return matches
        else:
            return self._parse_full_regular_response(response, qparams["fits_region_files"])


Most = MostClass()
