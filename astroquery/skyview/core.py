# Licensed under a 3-clause BSD style license - see LICENSE.rst
import pprint
from bs4 import BeautifulSoup
from six.moves.urllib import parse as urlparse
import six
from astropy import units as u

from . import conf
from ..query import BaseQuery
from ..utils import prepend_docstr_nosections, commons, async_to_sync


__doctest_skip__ = [
    'SkyViewClass.get_images',
    'SkyViewClass.get_images_async',
    'SkyViewClass.get_image_list']


@async_to_sync
class SkyViewClass(BaseQuery):
    URL = conf.url

    def __init__(self):
        super(SkyViewClass, self).__init__()
        self._default_form_values = None

    def _get_default_form_values(self, form):
        """
        Return the already selected values of a given form (a BeautifulSoup
        form node) as a dict.
        """
        res = []
        for elem in form.find_all(['input', 'select']):
            # ignore the submit and reset buttons
            if elem.get('type') in ['submit', 'reset']:
                continue
            # check boxes: enabled boxes have the value "on" if not specified
            # otherwise. Found out by debugging, perhaps not documented.
            if (elem.get('type') == 'checkbox' and
                    elem.get('checked') in ["", "checked"]):
                value = elem.get('value', 'on')
                res.append((elem.get('name'), value))
            # radio buttons and simple input fields
            if elem.get('type') == 'radio' and\
                    elem.get('checked') in ["", "checked"] or\
                    elem.get('type') in [None, 'text']:
                res.append((elem.get('name'), elem.get('value')))
            # dropdown menu, multi-section possible
            if elem.name == 'select':
                for option in elem.find_all('option'):
                    if option.get('selected') == '':
                        value = option.get('value', option.text.strip())
                        res.append((elem.get('name'), value))
        return {k: v
                for (k, v) in res
                if v not in [None, u'None', u'null'] and v
                }

    def _generate_payload(self, input=None):
        """
        Fill out the form of the SkyView site and submit it with the
        values given in ``input`` (a dictionary where the keys are the form
        element's names and the values are their respective values).
        """
        if input is None:
            input = {}
        form_response = self._request('GET', self.URL)
        bs = BeautifulSoup(form_response.content, "html.parser")
        form = bs.find('form')
        # cache the default values to save HTTP traffic
        if self._default_form_values is None:
            self._default_form_values = self._get_default_form_values(form)
        # only overwrite payload's values if the `input` value is not None
        # to avoid overwriting of the form's default values
        payload = self._default_form_values.copy()
        for k, v in six.iteritems(input):
            if v is not None:
                payload[k] = v
        url = urlparse.urljoin(self.URL, form.get('action'))
        return url, payload

    def _submit_form(self, input=None, cache=True):
        url, payload = self._generate_payload(input=input)
        response = self._request('GET', url, params=payload, cache=cache)
        return response

    def get_images(self, position, survey, coordinates=None, projection=None,
                   pixels=None, scaling=None, sampler=None, resolver=None,
                   deedger=None, lut=None, grid=None, gridlabels=None,
                   radius=None, height=None, width=None, cache=True,
                   show_progress=True):
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
        resolver : str
            The name resolver allows to choose a name resolver to use when
            looking up a name which was passed in the ``position`` parameter
            (as opposed to a numeric coordinate value). The default choice
            is to call the SIMBAD name resolver first and then the NED
            name resolver if the SIMBAD search fails.
        deedger : str
            When multiple input images with different backgrounds are
            resampled the edges between the images may be apparent because
            of the background shift. This parameter makes it possible to
            attempt to minimize these edges by applying a de-edging
            algorithm. The user can elect to choose the default given for
            that survey, to turn de-edging off, or to use the default
            de-edging algorithm. The supported values are: ``"_skip_"`` to
            use the survey default, ``"skyview.process.Deedger"`` (for
            enabling de-edging), and ``"null"`` to disable.
        lut : str
            Choose from the color table selections to display the data in
            false color.
        grid : bool
            overlay a coordinate grid on the image if True
        gridlabels : bool
            annotate the grid with coordinates positions if True
        radius : `~astropy.units.Quantity` or None
            The radius of the specified field.  Overrides width and height.
        width : `~astropy.units.Quantity` or None
            The width of the specified field.  Must be specified
            with ``height``.
        height : `~astropy.units.Quantity` or None
            The height of the specified field.  Must be specified
            with ``width``.

        References
        ----------
        .. [1] http://skyview.gsfc.nasa.gov/current/help/fields.html

        Examples
        --------
        >>> sv = SkyView()
        >>> paths = sv.get_images(position='Eta Carinae',
        ...                       survey=['Fermi 5', 'HRI', 'DSS'])
        >>> for path in paths:
        ...     print('\tnew file:', path)

        Returns
        -------
        A list of `~astropy.io.fits.HDUList` objects.

        """
        readable_objects = self.get_images_async(position, survey, coordinates,
                                                 projection, pixels, scaling,
                                                 sampler, resolver, deedger,
                                                 lut, grid, gridlabels,
                                                 radius=radius, height=height,
                                                 width=width,
                                                 cache=cache,
                                                 show_progress=show_progress)
        return [obj.get_fits() for obj in readable_objects]

    @prepend_docstr_nosections(get_images.__doc__)
    def get_images_async(self, position, survey, coordinates=None,
                         projection=None, pixels=None, scaling=None,
                         sampler=None, resolver=None, deedger=None, lut=None,
                         grid=None, gridlabels=None, radius=None, height=None,
                         width=None, cache=True, show_progress=True):
        """
        Returns
        -------
        A list of context-managers that yield readable file-like objects
        """
        image_urls = self.get_image_list(position, survey, coordinates,
                                         projection, pixels, scaling, sampler,
                                         resolver, deedger, lut, grid,
                                         gridlabels, radius=radius,
                                         height=height, width=width,
                                         cache=cache)
        return [commons.FileContainer(url, encoding='binary',
                                      show_progress=show_progress)
                for url in image_urls]

    @prepend_docstr_nosections(get_images.__doc__, sections=['Returns', 'Examples'])
    def get_image_list(self, position, survey, coordinates=None,
                       projection=None, pixels=None, scaling=None,
                       sampler=None, resolver=None, deedger=None, lut=None,
                       grid=None, gridlabels=None, radius=None, width=None,
                       height=None, cache=True):
        """
        Returns
        -------
        list of image urls

        Examples
        --------
        >>> SkyView().get_image_list(position='Eta Carinae',
        ...                          survey=['Fermi 5', 'HRI', 'DSS'])
        [u'http://skyview.gsfc.nasa.gov/tempspace/fits/skv6183161285798_1.fits',
         u'http://skyview.gsfc.nasa.gov/tempspace/fits/skv6183161285798_2.fits',
         u'http://skyview.gsfc.nasa.gov/tempspace/fits/skv6183161285798_3.fits']
        """

        self._validate_surveys(survey)

        if radius is not None:
            size_deg = str(radius.to(u.deg).value)
        elif width and height:
            size_deg = "{0},{1}".format(width.to(u.deg).value,
                                        height.to(u.deg).value)
        elif width and height:
            raise ValueError("Must specify width and height if you "
                             "specify either.")
        else:
            size_deg = None

        input = {
            'Position': parse_coordinates(position),
            'survey': survey,
            'Deedger': deedger,
            'lut': lut,
            'projection': projection,
            'gridlabels': '1' if gridlabels else '0',
            'coordinates': coordinates,
            'scaling': scaling,
            'grid': grid,
            'resolver': resolver,
            'Sampler': sampler,
            'imscale': size_deg,
            'size': size_deg,
            'pixels': pixels}
        response = self._submit_form(input, cache=cache)
        urls = self._parse_response(response)
        return urls

    def _parse_response(self, response):
        bs = BeautifulSoup(response.content, "html.parser")
        urls = []
        for a in bs.find_all('a'):
            if a.text == 'FITS':
                href = a.get('href')
                urls.append(urlparse.urljoin(response.url, href))
        return urls

    @property
    def survey_dict(self):
        if not hasattr(self, '_survey_dict'):

            response = self._request('GET', self.URL, cache=False)
            page = BeautifulSoup(response.content, "html.parser")
            surveys = page.findAll('select', {'name': 'survey'})

            self._survey_dict = {
                sel['id']: [x.text for x in sel.findAll('option')]
                for sel in surveys
                if 'overlay' not in sel['id']
            }

        return self._survey_dict

    @property
    def _valid_surveys(self):
        # Return a flat list of all valid surveys
        return [x for v in self.survey_dict.values() for x in v]

    def _validate_surveys(self, surveys):
        if not isinstance(surveys, list):
            surveys = [surveys]

        for sv in surveys:
            if sv not in self._valid_surveys:
                raise ValueError("Survey is not among the surveys hosted "
                                 "at skyview.  See list_surveys or "
                                 "survey_dict for valid surveys.")

    def list_surveys(self):
        """
        Print out a formatted version of the survey dict
        """
        pprint.pprint(self.survey_dict)


def parse_coordinates(position):
    coord = commons.parse_coordinates(position)
    return coord.fk5.to_string()


SkyView = SkyViewClass()
