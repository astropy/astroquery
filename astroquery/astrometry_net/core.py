# Licensed under a 3-clause BSD style license - see LICENSE.rst


import json

from astropy.io import fits
from astropy.stats import sigma_clipped_stats
from astropy.coordinates import SkyCoord

try:
    from astropy.nddata import CCDData
except ImportError:
    _HAVE_CCDDATA = False
else:
    _HAVE_CCDDATA = True

try:
    from photutils.detection import DAOStarFinder
except ImportError:
    _HAVE_SOURCE_DETECTION = False
else:
    _HAVE_SOURCE_DETECTION = True

from ..query import BaseQuery
from ..utils import async_to_sync, url_helpers
from ..exceptions import TimeoutError
from . import conf
import time


# export all the public classes and methods
__all__ = ['AstrometryNet', 'AstrometryNetClass']


MISSING_API_KEY = """
Astrometry.net API key not set. You should either set this in the astroquery configuration file using:

    [astrometry_net]
    api_key = ADD_YOUR_API_KEY_HERE

or you can set it for this session only using the ``conf`` object:

    from astroquery.astrometry_net import conf
    conf.api_key = 'ADD_YOUR_API_KEY_HERE'

or using the ``api_key`` property on the ``AstrometryNet`` class:

    from astroquery.astrometry_net import AstrometryNet
    AstrometryNet.api_key = 'ADD_YOUR_API_KEY_HERE'
""".lstrip()


@async_to_sync
class AstrometryNetClass(BaseQuery):
    """
    Perform queries to the astrometry.net service to fit WCS to images
    or source lists.
    """
    URL = conf.server
    TIMEOUT = conf.timeout
    API_URL = url_helpers.join(URL, 'api')

    # These are drawn from https://astrometry.net/doc/net/api.html#submitting-a-url
    _constraints = {
        'allow_commercial_use': {'default': 'd', 'type': str, 'allowed': ('d', 'y', 'n')},
        'allow_modifications': {'default': 'd', 'type': str, 'allowed': ('d', 'y', 'n')},
        'publicly_visible': {'default': 'y', 'type': str, 'allowed': ('y', 'n')},
        'scale_units': {'default': None, 'type': str, 'allowed': ('degwidth', 'arcminwidth', 'arcsecperpix')},
        'scale_type': {'default': None, 'type': str, 'allowed': ('ev', 'ul')},
        'scale_lower': {'default': None, 'type': float, 'allowed': (0,)},
        'scale_upper': {'default': None, 'type': float, 'allowed': (0,)},
        'scale_est': {'default': None, 'type': float, 'allowed': (0,)},
        'scale_err': {'default': None, 'type': float, 'allowed': (0, 100)},
        'center_ra': {'default': None, 'type': float, 'allowed': (0, 360)},
        'center_dec': {'default': None, 'type': float, 'allowed': (-90, 90)},
        'radius': {'default': None, 'type': float, 'allowed': (0,)},
        'downsample_factor': {'default': None, 'type': int, 'allowed': (1,)},
        'tweak_order': {'default': 2, 'type': int, 'allowed': (0,)},
        'use_sextractor': {'default': False, 'type': bool, 'allowed': ()},
        'crpix_center': {'default': None, 'type': bool, 'allowed': ()},
        'parity': {'default': None, 'type': int, 'allowed': (0, 2)},
        'positional_error': {'default': None, 'type': float, 'allowed': (0,)},
    }

    _no_source_detector = not _HAVE_SOURCE_DETECTION

    @property
    def api_key(self):
        """ Return the Astrometry.net API key. """
        if not conf.api_key:
            raise RuntimeError(MISSING_API_KEY)
        return conf.api_key

    @api_key.setter
    def api_key(self, value):
        """ Temporarily set the API key. """
        conf.api_key = value

    @property
    def empty_settings(self):
        """
        Construct a dict of settings using the defaults
        """
        return {k: self._constraints[k]['default'] for k in self._constraints.keys()}

    def show_allowed_settings(self):
        """
        There are a ton of options available for solving. This displays
        them in a nice way.
        """
        keys = sorted(self._constraints.keys())
        for key in keys:
            key_info = self._constraints[key]
            print('{key}: type {type!r}, '
                  'default value {default}, '
                  'allowed values {values}'
                  ''.format(key=key,
                            type=key_info['type'].__name__,
                            default=key_info['default'],
                            values=key_info['allowed']))

    def __init__(self):
        super().__init__()
        self._session_id = None

    def _login(self):
        login_url = url_helpers.join(self.API_URL, 'login')
        payload = self._construct_payload({'apikey': self.api_key})
        result = self._request('POST', login_url,
                               data=payload,
                               cache=False)
        result_dict = result.json()
        if result_dict['status'] != 'success':
            raise RuntimeError('Unable to log in to astrometry.net')
        self._session_id = result_dict['session']

    def _construct_payload(self, settings):
        return {'request-json': json.dumps(settings)}

    def _validate_settings(self, settings):
        """
        Check whether the current settings are consistent with the choices available
        from astrometry.net.
        """

        # Check the types and values
        for key, value in settings.items():
            if key not in self._constraints or value is None:
                message = ('Setting {} is not allowed. Display all of '
                           'the allowed settings with: '
                           'AstrometryNet.show_allowed_settings()'.format(key))
                raise ValueError(message)
            if not isinstance(value, self._constraints[key]['type']):
                failed = True
                # Try coercing the type...
                if self._constraints[key]['type'] == float:
                    try:
                        _ = self._constraints[key]['type'](value)
                    except ValueError:
                        pass
                    else:
                        failed = False
                if failed:
                    raise ValueError('Value for {} must be of type {}'.format(key, self._constraints[key]['type']))
            # Switching on the types here...not fond of this, but it works.
            allowed = self._constraints[key]['allowed']
            if allowed:
                if self._constraints[key]['type'] == str:
                    # Allowed values is a list of choices.
                    good_value = value in self._constraints[key]['allowed']
                elif self._constraints[key]['type'] == bool:
                    # bool is easy to check...
                    good_value = isinstance(value, bool)
                else:
                    # Assume the parameter is a number which has a minimum and
                    # optionally a maximum.
                    bounds = self._constraints[key]['allowed']
                    good_value = value >= bounds[0]
                    try:
                        good_value = good_value and good_value <= bounds[1]
                    except IndexError:
                        # No upper bound to check
                        pass
                if not good_value:
                    raise ValueError('Value {} for {} is invalid. '
                                     'The valid '
                                     'values are {}'.format(value, key, allowed))
        # Check some special cases, in which the presence of one value means
        # others are needed.
        if 'scale_type' in settings:
            scale_type = settings['scale_type']
            if scale_type == 'ev':
                required_keys = ['scale_est', 'scale_err', 'scale_units']
            else:
                required_keys = ['scale_lower', 'scale_upper', 'scale_units']
            good = all(req in settings for req in required_keys)
            if not good:
                raise ValueError('Scale type {} requires '
                                 'values for {}'.format(scale_type, required_keys))

    def monitor_submission(self, submission_id, *,
                           solve_timeout=TIMEOUT, verbose=True, return_submission_id=False):
        """
        Monitor the submission for completion.

        Parameters
        ----------

        submission_id : ``int`` or ``str``
            Submission ID number from astrometry.net.
        solve_timeout : ``int``
            Time, in seconds, to wait for the astrometry.net solver to find
            a solution.
        verbose : bool, optional
            Whether to print out information about the solving.
        return_submission_id : bool, optional
            Whether to return the Submission ID number.

        Returns
        -------

        None or `~astropy.io.fits.Header` or (`~astropy.io.fits.Header`, str)
            The contents of the returned object depend on whether the solve
            succeeds or fails. If the solve succeeds the header with
            the WCS solution generated by astrometry.net is returned. A tuple
            containing WCS solution and Submission ID is return if the
            return_submission_id parameter is set True. If the solve
            fails then an empty dictionary is returned. See below for the outcome
            if the solve times out.

        Raises
        ------

        ``TimeoutError``
            Raised if `astroquery.astrometry_net.AstrometryNetClass.TIMEOUT` is
            exceeded before the solve either succeeds or fails. The second
            argument in the exception is the submission ID.
        """
        has_completed = False
        job_id = None
        if verbose:
            print('Solving', end='', flush=True)
        start_time = time.time()
        status = ''
        while not has_completed:
            time.sleep(1)
            sub_stat_url = url_helpers.join(self.API_URL, 'submissions', str(submission_id))
            sub_stat = self._request('GET', sub_stat_url, cache=False)
            jobs = sub_stat.json()['jobs']
            if jobs:
                job_id = jobs[0]
            if job_id:
                job_stat_url = url_helpers.join(self.API_URL, 'jobs',
                                                str(job_id), 'info')
                job_stat = self._request('GET', job_stat_url, cache=False)
                status = job_stat.json()['status']
            now = time.time()
            elapsed = now - start_time
            timed_out = elapsed > solve_timeout
            has_completed = (status in ['success', 'failure'] or timed_out)
            if verbose:
                print('.', end='', flush=True)
        if status == 'success':
            wcs_url = url_helpers.join(self.URL, 'wcs_file', str(job_id))
            wcs_response = self._request('GET', wcs_url)
            wcs = fits.Header.fromstring(wcs_response.text)
        elif status == 'failure':
            wcs = {}
        elif timed_out:
            raise TimeoutError('Solve timed out without success or failure',
                               submission_id)
        else:
            # Try to future-proof a little bit
            raise RuntimeError('Unrecognized status {}'.format(status))
        if return_submission_id is False:
            return wcs
        else:
            return (wcs, submission_id)

    def solve_from_source_list(self, x, y, image_width, image_height, *,
                               solve_timeout=TIMEOUT,
                               verbose=True,
                               return_submission_id=False,
                               **settings
                               ):
        """
        Plate solve from a list of source positions.

        Parameters
        ----------

        x : list-like
            List of x-coordinate of source positions.
        y : list-like
            List of y-coordinate of source positions.
        image_width : int
            Size of the image in the x-direction.
        image_height : int
            Size of the image in the y-direction.
        solve_timeout : int
            Time, in seconds, to wait for the astrometry.net solver to find
            a solution.
        verbose : bool, optional
            Whether to print out information about the solving.
        return_submission_id : bool, optional
            Whether to return the Submission ID number.

        For a list of the remaining settings, use the method
        `~AstrometryNetClass.show_allowed_settings`.
        """
        settings = {k: v for k, v in settings.items() if v is not None}
        self._validate_settings(settings)
        if self._session_id is None:
            self._login()
        # Add the settings required for solving from a source list to the list
        # after validating the common settings applicable in all cases.
        settings['x'] = [float(v) for v in x]
        settings['y'] = [float(v) for v in y]
        settings['image_width'] = image_width
        settings['image_height'] = image_height
        settings['session'] = self._session_id
        payload = self._construct_payload(settings)
        url = url_helpers.join(self.API_URL, 'url_upload')
        response = self._request('POST', url, data=payload, cache=False)
        if response.status_code != 200:
            raise RuntimeError('Post of job failed')
        response_d = response.json()
        submission_id = response_d['subid']
        return self.monitor_submission(submission_id,
                                       solve_timeout=solve_timeout,
                                       verbose=verbose,
                                       return_submission_id=return_submission_id)

    def solve_from_image(self, image_file_path, *, force_image_upload=False,
                         ra_key=None, dec_key=None,
                         ra_dec_units=None,
                         fwhm=3, detect_threshold=5,
                         solve_timeout=TIMEOUT,
                         verbose=True,
                         return_submission_id=False,
                         **settings):
        """
        Plate solve from an image, either by uploading the image to
        astrometry.net or by finding sources locally using
        `photutils <https://photutils.rtfd.io>`_ and solving with source
        locations.

        Parameters
        ----------

        image_file_path : str or Path object
            Path to the image.

        force_image_upload : bool, optional
            If ``True``, upload the image to astrometry.net even if it is
            possible to detect sources in the image locally. This option will
            almost always take longer than finding sources locally. It will even
            take longer than installing photutils and then rerunning this.

            Even if this is ``False`` the image will be upload unless
            photutils is installed.

        ra_key : str, optional
            Name of the key in the FITS header that contains right ascension of the image.
            The ra can be specified using the ``center_ra`` setting instead if
            desired.

        dec_key : str, optional
            Name of the key in the FITS header that contains declination of the image.
            The dec can be specified using the ``center_dec`` setting instead if
            desired.

        ra_dec_units : tuple, optional
            Tuple specifying the units of the right ascension and declination in
            the header. The default value is ``('hour', 'degree')``.

        solve_timeout : int
            Time, in seconds, to wait for the astrometry.net solver to find
            a solution.

        verbose : bool, optional
            Whether to print out information about the solving.

        return_submission_id : bool, optional
            Whether to return the Submission ID number.

        For a list of the remaining settings, use the method
        `~AstrometryNetClass.show_allowed_settings`.
        """
        if ra_key and dec_key:
            with fits.open(image_file_path) as f:
                hdr = f[0].header
                # The error here if one of these fails should be pretty clear
                ra = hdr[ra_key]
                dec = hdr[dec_key]
                # Convert these to degrees in appropriate range
                center = SkyCoord(ra, dec, unit=('hour', 'degree'))
                settings['center_ra'] = center.ra.degree
                settings['center_dec'] = center.dec.degree

        settings = {k: v for k, v in settings.items() if v is not None}
        self._validate_settings(settings)

        if force_image_upload or self._no_source_detector:
            if self._session_id is None:
                self._login()
            settings['session'] = self._session_id
            payload = self._construct_payload(settings)
            url = url_helpers.join(self.API_URL, 'upload')
            with open(image_file_path, 'rb') as f:
                response = self._request('POST', url, data=payload,
                                         cache=False,
                                         files={'file': f})
        else:
            # Detect sources and delegate to solve_from_source_list
            if _HAVE_CCDDATA:
                # CCDData requires a unit, so provide one. It has absolutely
                # no impact on source detection. The reader for CCDData
                # tries to find the first ImageHDU in a FITS file, so it
                # is the preferred way to get the data.
                ccd = CCDData.read(image_file_path, unit='adu')
                data = ccd.data
            else:
                with fits.open(image_file_path) as f:
                    data = f[0].data
            if verbose:
                print("Determining background stats", flush=True)
            mean, median, std = sigma_clipped_stats(data, sigma=3.0,
                                                    maxiters=5)
            daofind = DAOStarFinder(fwhm=fwhm,
                                    threshold=detect_threshold * std)
            if verbose:
                print("Finding sources", flush=True)
            sources = daofind(data - median)
            if verbose:
                print('Found {} sources'.format(len(sources)), flush=True)
            # astrometry.net wants a sorted list of sources
            # Sort first (which puts things in ascending order)
            sources.sort('flux')
            # Reverse to get descending order
            sources.reverse()
            if verbose:
                print(sources)

            # It turns out astrometry.net is 1-indexed, so add 1 to the source positions.
            sources['xcentroid'] += 1
            sources['ycentroid'] += 1
            return self.solve_from_source_list(sources['xcentroid'],
                                               sources['ycentroid'],
                                               ccd.header['naxis1'],
                                               ccd.header['naxis2'],
                                               solve_timeout=solve_timeout,
                                               verbose=verbose,
                                               return_submission_id=return_submission_id,
                                               **settings)
        if response.status_code != 200:
            raise RuntimeError('Post of job failed')
        response_d = response.json()
        submission_id = response_d['subid']
        return self.monitor_submission(submission_id,
                                       solve_timeout=solve_timeout,
                                       verbose=verbose,
                                       return_submission_id=return_submission_id)


# the default tool for users to interact with is an instance of the Class
AstrometryNet = AstrometryNetClass()
