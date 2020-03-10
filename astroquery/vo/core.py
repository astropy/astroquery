# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
VoImageQuery
====

Module to query a data centre using IVOA standards compatible services:
- IVO Registry to find the service
- SIAv2 to query the service for metadata,
- ObsCore results format to filter on
- DataLink to retrieve information regarding the actual data (format, size...)
- SODA to access the data and perform service operations such as cutouts.
On the client side, the IVOA functionality is provided by the astropy `pyvo`
package. This is an example of combining these protocols to implement the
generic astroquery API.
"""

import logging
import warnings
import shutil
import os
from astropy.io.fits import HDUList
from astropy.utils.exceptions import AstropyDeprecationWarning
from astropy import units as u
from ..query import BaseQuery

try:
    import pyvo
except ImportError:
    print('Please install pyvo. astropy.vo does not work without it.')
except AstropyDeprecationWarning as e:
    if str(e) == \
            'The astropy.vo.samp module has now been moved to astropy.samp':
        print('AstropyDeprecationWarning: {}'.format(str(e)))
    else:
        raise e

__all__ = ['VoImageQuery']


logger = logging.getLogger(__name__)

# TODO figure out what do to if anything about them. Some might require
# fixes on the servers
warnings.filterwarnings('ignore', module='astropy.io.votable')


class VoImageQuery(BaseQuery):
    """
    Class for querying image data based using a SIAv2 service and other IVOA
    services and protocols. Typical usage:

    client = VoImageQuery(authority_id='ivo://cadc.nrc.ca/sia')

    result = client.query_region('08h45m07.5s +54d18m00s',
                                 collection='CFHT')

    ... do something with result (optional) and get the URLs of all the
        associated data

    urls = client.get_data_urls(result, types=None)

    ... or just the URLS of the data files
    urls = client.get_data_urls(result)

    ... download data or...

    ... download data that intersects given coordinates (cutouts)

    list_hdulist = client.get_images(result, dest_dir, pos=(1, 2, 3))
    """

    def __init__(self, authority_id=None, sia_service_url=None, session=None):
        """
        Initialize the ImageQuery object

        Parameters
        ----------
        authority_id : str, required if si_standard is the default standard ID
            or a different standard ID
        sia_service_url : str, access URL to the SIA service to use.
        Returns
        -------
        Vo object that can be used to query for data
        """
        if not sia_service_url:
            # look it up in the registry
            sia_service_url = VoImageQuery.find_service_url(authority_id)
        super(VoImageQuery, self).__init__()
        self.sia_service = pyvo.dal.sia2.SIAService(baseurl=sia_service_url,
                                                    session=session)
        self._download_errors = []  # recorded download errors

    @property
    def download_errors(self):
        """
        Called to check the error messages encountered during the execution
        of `get_images`.
        """
        return self._download_errors

    def find_service_url(authority_id):
        """
        Find the SIAv2 service url corresponding to an authority_id
        """
        if authority_id is None:
            raise AttributeError(
                "Either authority ID or the URL to sia service required")
        else:
            # need to lookup the access url
            query = pyvo.registry.regtap.RegistryQuery(
                pyvo.registry.regtap.REGISTRY_BASEURL,
                "SELECT access_url, authenticated_only "
                "FROM rr.capability NATURAL JOIN rr.interface "
                "WHERE ivoid LIKE '{}%' "
                "AND lower(standard_id)='{}' "
                "AND intf_role='std'".format(
                    authority_id, pyvo.dal.sia2.SIA2_STANDARD_ID.lower()))
            result = query.execute()
            if len(result) < 1:
                raise AttributeError(
                    'No access URL for authority ID {} and SIA '
                    'standard {}'.format(authority_id,
                                         pyvo.dal.sia2.SIA2_STANDARD_ID))
            sia_service_url = \
                result[0].get('access_url', decode=True)

        return sia_service_url
        # self.authenticated_only = 0 #TODO how to figure out? Capabilities?

    def query_region(self, coordinates=None, radius=None,
                     pos=None, band=None, time=None, pol=None,
                     field_of_view=None, spatial_resolution=None,
                     spectral_resolving_power=None, exptime=None,
                     timeres=None, publisher_did=None, facility=None,
                     collection=None,
                     instrument=None, data_type=None, calib_level=None,
                     target_name=None, res_format=None, maxrec=None
                     ):
        """
        Queries the SIA service for a region around the specified coordinates
        and return results in ObsCore format.

        Parameters
        ----------
        coordinates : `astropy.coordinates.SkyCoord` or value that can be
            turned into SkyCoord. In addition, it accepts sequence of numbers
            representing expressing ra and dec in icrs degrees
            coordinates around which to query
        radius : str or `astropy.units.Quantity`.
            the radius of the cone search
                _SIA2_PARAMETERS


        Returns
        -------
        response : `pyvo.dal.sia2.SIAResults` type
        """

        if coordinates:
            if not radius:
                radius = 0.016666666666667*u.deg
            circle = (coordinates.ra.to(u.deg),
                      coordinates.dec.to(u.deg), radius.to(u.deg))
            if pos:
                pos.append(circle)
            else:
                pos = circle
        return self.sia_service.search(
            pos=pos,
            band=band,
            time=time,
            pol=pol,
            field_of_view=field_of_view,
            spatial_resolution=spatial_resolution,
            spectral_resolving_power=spectral_resolving_power,
            exptime=exptime,
            timeres=timeres,
            publisher_did=publisher_did,
            facility=facility,
            collection=collection,
            instrument=instrument,
            data_type=data_type,
            calib_level=calib_level,
            target_name=target_name,
            res_format=res_format,
            maxrec=maxrec)

    query_region.__doc__ = query_region.__doc__.replace(
        '_SIA2_PARAMETERS', pyvo.dal.sia2.SIA_PARAMETERS_DESC)

    def get_data_urls(self, sia_results, types="#this"):
        """
        Function to return list of files corresponding to the the results of
        a previously run SIA2 query.

        Parameters
        ----------

        sia_results: `pyvo.dal.sia2.SIAResults` instance
            results obtain from a previous SIA query.
        types: str or list of str
            list of file types to filter on or no filtering if None.
            TODO: provide possible values

        Returns
        -------
        List of `pyvo.dal.DatalinkRecord` instances. Besides the `access_url`
        attribute, the instances contain information regarding content length,
        type and description of the file.s

        """
        if types and not isinstance(types, list):
            types = [types]
        results = []
        try:
            for dl in sia_results.iter_datalinks():
                if types:
                    for tt in types:
                        results += [x for x in dl.bysemantics(tt)]
                else:
                    results += [x for x in dl]
        finally:
            sia_results.reset_datalinks_iter()
        return results

    def get_images(self, sia_results, dest_dir, pos=None, band=None,
                   time=None, pol=None, stop_on_error=False):
        """
        A function that downloads the image files corresponding to the results
        of an SIA query execution.

        Parameters
        ----------
        sia_results: `pyvo.dal.sia2.SIAResults` instance
            results obtain from a previous SIA query.
        dest_dir: `os.path`
            location to save the files to
        pos : single or list of tuples
            angle units (default: deg)
            the positional region(s) to be searched for data. Each region can
            be expressed as a tuple representing a CIRCLE, RANGE or POLYGON as
            follows:
            (ra, dec, radius) - for CIRCLE. (angle units - defaults to)
            (long1, long2, lat1, lat2) - for RANGE (angle units required)
            (ra, dec, ra, dec, ra, dec ... ) ra/dec points for POLYGON all
            in angle units
        band : scalar, tuple(interval) or list of tuples
            (spectral units (default: meter)
            the energy interval(s) to be searched for data.
        time : single or list of `~astropy.time.Time` or compatible strings
            the time interval(s) to be searched for data.
        pol : single or list of str from `pyvo.dam.obscore.POLARIZATION_STATES`
            the polarization state(s) to be searched for data.
        stop_on_error: boolean
            when True, method exits when first error encountered otherwise
            it continues with the next record and records errors in the
            `download_errors` property.

        Returns
        -------
        list : A list of `~astropy.io.fits.HDUList` objects (or a list of
        str if returning urls).
        """
        if not os.path.isdir(dest_dir):
            raise ValueError(
                '{} is not a valid destination directory'.format(dest_dir))

        results = []
        self._download_errors[:] = []
        if pos:
            if not isinstance(pos, list):
                pos = [pos]
            pp = pyvo.dal.params.PosQueryParam(pos)
            pos = pp.dal
        if band:
            bb = pyvo.dal.params.BandQueryParam(band)
            band = bb.dal
        if time:
            tt = pyvo.dal.params.TimeQueryParam(time)
            time = tt.dal
        if pol:
            po = pyvo.dal.params.PolQueryParam(pol)
            pol = po.dal

        try:
            for dl in sia_results.iter_datalinks():
                try:
                    self._get_file(band, dest_dir, dl, pol, pos, results, time)
                except Exception as e:
                    if stop_on_error:
                        raise e
                    self._download_errors.append(str(e))
                    logger.warning('Cannot get file {}: {}'.format(dl[0].id,
                                                                   str(e)))
        finally:
            sia_results.reset_datalinks_iter()

        return results

    def _get_file(self, band, dest_dir, dl, pol, pos, results, time):
        if pos or band or time or pol:
            # cutouts
            soda_cutouts = []
            for rr in dl:
                if rr.get('semantics', decode=True) == "#cutout":
                    soda_cutouts.append(rr.get('service_def', decode=True))
            if not soda_cutouts:
                raise RuntimeError(
                    'No cutout service found for {}. Try downloading the '
                    'entire file (no cutout args)'.format(dl[0].id))
            soda_cutout = None
            for ff in dl.bysemantics('#cutout'):
                # only sync cutout service for now
                if ff.service_def not in soda_cutouts:
                    continue
                for _ in ff.params:
                    if _.ID == 'standardID' and _.value.decode('utf-8') == \
                            pyvo.dal.adhoc.SODA_SYNC_IVOID:
                        soda_cutout = ff
                        break
            if soda_cutout:
                instream = soda_cutout.processed(pos=pos, band=band,
                                                 time=time, pol=pol)
            else:
                raise RuntimeError(
                    'No sync cutout service found for {}. Try to download '
                    'entire files (no cutout args)'.format(dl[0].id))
        else:
            instream = list(dl.bysemantics('#this'))[0].processed()
        if instream:
            # no content disposition available, use IDs by making them
            # compatible with file names
            file_name = instream.id.replace("/", "_")
            local_file = os.path.join(dest_dir, file_name)
            logger.debug(
                'Saving ID {} as file {}'.format(dl[0].id, local_file))
            with open(local_file, 'wb') as f:
                shutil.copyfileobj(instream, f)
                results.append(HDUList.fromfile(local_file))
        else:
            raise RuntimeError('Could not download file {}'.format(dl[0].id))
