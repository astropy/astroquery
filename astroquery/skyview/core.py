# Licensed under a 3-clause BSD style license - see LICENSE.rst
import requests
from bs4 import BeautifulSoup
from astropy.extern.six.moves.urllib import parse as urlparse
from astropy.extern import six
from . import conf
from ..query import BaseQuery
from ..utils import prepend_docstr_noreturns, commons, async_to_sync


__doctest_skip__ = [
    'SkyViewClass.get_images',
    'SkyViewClass.get_images_async',
    'SkyViewClass.get_image_list']


@async_to_sync
class SkyViewClass(BaseQuery):
    URL = conf.url

    def __init__(self):
        BaseQuery.__init__(self)
        self._default_form_values = None

    def _get_default_form_values(self, form):
        """Return the already selected values of a given form (a BeautifulSoup
        form node) as a dict.

        """
        res = []
        for elem in form.find_all(['input', 'select']):
            # ignore the submit and reset buttons
            if elem.get('type') in ['submit', 'reset']:
                continue
            # check boxes: enabled boxes have the value "on" if not specificed
            # otherwise. Found out by debugging, perhaps not documented.
            if elem.get('type') == 'checkbox' and elem.get('checked') in ["", "checked"]:
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
        return dict(
            (k, v) for (k, v) in res if v not in [None, u'None', u'null'] and v
        )

    def _submit_form(self, input=None):
        """Fill out the form of the SkyView site and submit it with the
        values given in `input` (a dictionary where the keys are the form
        element's names and the values are their respective values).

        """
        if input is None:
            input = {}
        response = requests.get(self.URL)
        bs = BeautifulSoup(response.text)
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
        response = requests.get(url, params=payload)
        return response

    def get_images(
            self, position, survey, coordinates=None, projection=None,
            pixels=None, scaling=None, sampler=None, resolver=None,
            deedger=None, lut=None, grid=None, gridlabels=None):
        """Query the SkyView service, download the FITS file that will be
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
            looking up a name which was passed in the `position` parameter
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
            annotate the grid with coordinates postions if True

        References
        ----------
        .. [1] http://skyview.gsfc.nasa.gov/current/help/fields.html

        Examples
        --------
        >>> sv = SkyView()
        >>> paths = sv.get_images(position='Eta Carinae', survey=['Fermi 5', 'HRI', 'DSS'])
        >>> for path in paths:
        ...     print '\tnew file:', path

        Returns
        -------
        A list of `astropy.fits.HDUList` objects

        """
        readable_objects = self.get_images_async(
            position, survey, coordinates, projection,
            pixels, scaling, sampler, resolver,
            deedger, lut, grid, gridlabels)
        return [obj.get_fits() for obj in readable_objects]

    @prepend_docstr_noreturns(get_images.__doc__)
    def get_images_async(
            self, position, survey, coordinates=None, projection=None,
            pixels=None, scaling=None, sampler=None, resolver=None,
            deedger=None, lut=None, grid=None, gridlabels=None):
        """
        Returns
        -------
        A list of context-managers that yield readable file-like objects
        """
        image_urls = self.get_image_list(
            position, survey, coordinates, projection,
            pixels, scaling, sampler, resolver,
            deedger, lut, grid, gridlabels)
        return [commons.FileContainer(url) for url in image_urls]

    @prepend_docstr_noreturns(get_images.__doc__)
    def get_image_list(
            self, position, survey, coordinates=None, projection=None,
            pixels=None, scaling=None, sampler=None, resolver=None,
            deedger=None, lut=None, grid=None, gridlabels=None):
        """
        Returns
        -------
        list of image urls

        Examples
        --------
        >>> SkyView().get_image_list(position='Eta Carinae', survey=['Fermi 5', 'HRI', 'DSS'])
        [u'http://skyview.gsfc.nasa.gov/tempspace/fits/skv6183161285798_1.fits',
         u'http://skyview.gsfc.nasa.gov/tempspace/fits/skv6183161285798_2.fits',
         u'http://skyview.gsfc.nasa.gov/tempspace/fits/skv6183161285798_3.fits']
        """
        input = {
            'Position': position,
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
            'pixels': pixels}
        response = self._submit_form(input)
        urls = self._parse_response(response)
        return urls

    def _parse_response(self, response):
        bs = BeautifulSoup(response.content)
        urls = []
        for a in bs.find_all('a'):
            if a.text == 'FITS':
                href = a.get('href')
                urls.append(urlparse.urljoin(response.url, href))
        return urls

SkyView = SkyViewClass()
