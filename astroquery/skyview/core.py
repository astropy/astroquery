# Licensed under a 3-clause BSD style license - see LICENSE.rst
from astropy import units as u
from astropy.utils.decorators import deprecated_renamed_argument
from pyvo import registry

from ..query import BaseQuery
from ..utils import prepend_docstr_nosections, commons, async_to_sync


__doctest_skip__ = [
    'SkyViewClass.get_images',
    'SkyViewClass.get_images_async',
    'SkyViewClass.get_image_list']


@async_to_sync
class SkyViewClass(BaseQuery):

    def __init__(self):
        super().__init__()

    @deprecated_renamed_argument(
        ('width', 'height', 'resolver', 'deedger', 'lut', 'grid', 'gridlabels'),
        (None, None, None, None, None, None, None),
        since=("0.4.7", "0.4.7", "0.4.7", "0.4.7", "0.4.7", "0.4.7", "0.4.7"))
    def get_images(self, position, survey, *, coordinates=None,
                   projection=None, pixels=None,
                   scaling=None, sampler=None, radius=None,
                   cache=True, show_progress=True,
                   width=None, height=None, resolver=None,
                   deedger=None, lut=None, grid=None, gridlabels=None):
        """
        Query the SkyView service, download the FITS file that will be
        found and return a generator over the local paths to the
        downloaded FITS files.

        Note that the files will be downloaded when the generator will be
        exhausted, i.e. just calling this method alone without iterating
        over the result won't issue a connection to the SkyView server.

        Parameters
        ----------
        position : str
            Determines the center of the field to be retrieved. Both
            coordinates (also equatorial ones) and object names are
            supported. Object names are converted to coordinates via the
            SIMBAD or NED name resolver. See the reference for more info
            on the supported syntax for coordinates.
        survey : str or list of str
            Select data from one or more surveys. The number of surveys
            determines the number of resulting file downloads. Passing a
            list with just one string has the same effect as passing this
            string directly.
        coordinates : str
            Choose among common equatorial, galactic and ecliptic
            coordinate systems (``"J2000"``, ``"B1950"``, ``"Galactic"``,
            ``"E2000"``, ``"ICRS"``) or pass a custom string.
        projection : str
            Choose among the map projections (the value in parentheses
            denotes the string to be passed):

            Gnomonic (Tan), default value
                good for small regions
            Rectangular (Car)
                simplest projection
            Aitoff (Ait)
                Hammer-Aitoff, equal area projection good for all sky maps
            Orthographic (Sin)
                Projection often used in interferometry
            Zenith Equal Area (Zea)
                equal area, azimuthal projection
            COBE Spherical Cube (Csc)
                Used in COBE data
            Arc (Arc)
                Similar to Zea but not equal-area
        pixels : str
            Selects the pixel dimensions of the image to be produced. A
            scalar value or a pair of values separated by comma may be
            given. If the value is a scalar the number of width and height
            of the image will be the same. By default a 300x300 image is
            produced.
        scaling : str
            Selects the transformation between pixel intensity and
            intensity on the displayed image. The supported values are:
            ``"Log"``, ``"Sqrt"``, ``"Linear"``, ``"HistEq"``,
            ``"LogLog"``.
        sampler : str
            The sampling algorithm determines how the data requested will
            be resampled so that it can be displayed.
        radius : `~astropy.units.Quantity` or None
            The angular radius of the specified field.

        References
        ----------
        .. [1] http://skyview.gsfc.nasa.gov/current/help/fields.html

        Examples
        --------
        >>> sv = SkyView()
        >>> paths = sv.get_images(position='Eta Carinae',
        ...                       survey=['HRI', 'DSS'])
        >>> for path in paths:
        ...     print('\tnew file:', path)

        Returns
        -------
        A list of `~astropy.io.fits.HDUList` objects.

        """
        readable_objects = self.get_images_async(position, survey, coordinates=coordinates,
                                                 projection=projection, pixels=pixels,
                                                 scaling=scaling, sampler=sampler, radius=radius,
                                                 cache=cache, show_progress=show_progress)
        return [obj.get_fits() for obj in readable_objects]

    @deprecated_renamed_argument(
        ('width', 'height', 'resolver', 'deedger', 'lut', 'grid', 'gridlabels'),
        (None, None, None, None, None, None, None),
        since=("0.4.7", "0.4.7", "0.4.7", "0.4.7", "0.4.7", "0.4.7", "0.4.7"))
    @prepend_docstr_nosections(get_images.__doc__)
    def get_images_async(self, position, survey, *, coordinates=None,
                         projection=None, pixels=None,
                         scaling=None, sampler=None, radius=None,
                         cache=True, show_progress=True,
                         width=None, height=None, resolver=None,
                         deedger=None, lut=None, grid=None, gridlabels=None):
        """
        Returns
        -------
        A list of context-managers that yield readable file-like objects
        """
        image_urls = self.get_image_list(position, survey, coordinates=coordinates,
                                         projection=projection, pixels=pixels, scaling=scaling,
                                         sampler=sampler, radius=radius,
                                         cache=cache)
        return [commons.FileContainer(url, encoding='binary',
                                      show_progress=show_progress)
                for url in image_urls]

    @deprecated_renamed_argument(
        ('width', 'height', 'resolver', 'deedger', 'lut', 'grid', 'gridlabels'),
        (None, None, None, None, None, None, None),
        since=("0.4.7", "0.4.7", "0.4.7", "0.4.7", "0.4.7", "0.4.7", "0.4.7"))
    @prepend_docstr_nosections(get_images.__doc__, sections=['Returns', 'Examples'])
    def get_image_list(self, position, survey, *, coordinates=None,
                       projection=None, pixels=None, scaling=None,
                       sampler=None, radius=None,
                       cache=True,
                       width=None, height=None, resolver=None,
                       deedger=None, lut=None, grid=None, gridlabels=None):
        """
        Returns
        -------
        list of image urls

        Examples
        --------
        >>> SkyView().get_image_list(position='Eta Carinae',
        ...                          survey=['HRI', 'DSS'])
        ['https://skyview.gsfc.nasa.gov/cgi-bin/images?position=161.26474075372%2C-59.6844587777
          &survey=dss&pixels=300%2C300&sampler=LI&size=1.0%2C1.0&projection=Tan
          &coordinates=J2000.0&requestID=skv1696445832839&return=FITS']
        """

        self._validate_surveys(survey)

        urls = []
        for current_survey in survey:
            registry_results = registry.search(ivoid=self._survey_dict[current_survey]['ivoid'])
            if len(registry_results) > 1:
                raise ValueError("Multiple surveys returned, ambiguous service")
            sia_service = registry_results[0].get_service()

            skyview_args = self._args_to_payload(position=position, coordinates=coordinates,
                                                 projection=projection, pixels=pixels,
                                                 scaling=scaling, sampler=sampler, radius=radius,
                                                 cache=cache)

            query_results = sia_service.search(**skyview_args)

            for result in query_results:
                urls.append(result.getdataurl())

        return urls

    def _args_to_payload(self, **kwargs):
        '''Convert arguments to supported pyVO parameters'''
        validated_args = dict()

        # Parse position arg to SkyCoord
        validated_args['pos'] = parse_coordinates(kwargs.pop('position'))

        # Calculate size param
        if kwargs.get('radius', None) is not None:
            validated_args['size'] = kwargs.pop('radius').to(u.deg).value * 2

        # Copy the remainder of the args, but also
        # Strip all "None" args and rely on downstream defaults
        validated_args.update({k: v for k, v in kwargs.items() if v is not None})

        # Force FITS return
        validated_args['format'] = "image/fits"

        return validated_args

    @property
    def survey_dict(self):
        if not hasattr(self, '_survey_dict'):
            self._survey_dict = {}

            sia_services = registry.search(registry.Servicetype('sia'))
            for service in sia_services:
                if service.ivoid.startswith('ivo://nasa.heasarc/skyview'):
                    self._survey_dict[service.short_name] = {'ivoid': service.ivoid, 'res_title': service.res_title}

        return self._survey_dict

    @property
    def _valid_surveys(self):
        # Return a list of all valid surveys
        return self.survey_dict.keys()

    def _validate_surveys(self, surveys):
        if not isinstance(surveys, list):
            surveys = [surveys]

        for sv in surveys:
            if sv not in self._valid_surveys:
                raise ValueError(f"Survey {sv} is not among the surveys "
                                 "hosted at skyview.  See list_surveys "
                                 "or survey_dict for valid surveys.")

    def list_surveys(self):
        """
        Returns a list of all valid SkyView surveys known to the pyVO registry
        """
        return list(self._valid_surveys)


def parse_coordinates(position):
    return commons.parse_coordinates(position)


SkyView = SkyViewClass()
