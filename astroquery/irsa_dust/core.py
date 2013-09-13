# Licensed under a 3-clause BSD style license - see LICENSE.rst
from astropy.table import Table, Column
import astropy.units as u
import astropy.utils.data as aud
import astropy.coordinates as coord
from astropy.io import fits
from . import utils
from . import IRSA_DUST_SERVER, IRSA_DUST_TIMEOUT
from ..utils.class_or_instance import class_or_instance
from ..utils import commons
from ..query import BaseQuery


# TODO Add support for server url from JSON cache
__all__ = ["IrsaDust"]

EXT_DESC = "E(B-V) Reddening"
EM_DESC = "100 Micron Emission"
TEMP_DESC = "Dust Temperature"

INPUT = "input"
OBJ_NAME = "objname"
REG_SIZE = "regSize"
DESC = "desc"
IMAGE_URL = "imageUrl"

STATISTICS = "statistics"
REF_PIXEL_VALUE = "refPixelValue"
REF_COORDINATE = "refCoordinate"
MEAN_VALUE = "meanValue"
STD = "std"
MAX_VALUE = "maxValue"
MIN_VALUE = "minValue"

DATA_IMAGE = "./data/image"
DATA_TABLE = "./data/table"


class IrsaDust(BaseQuery):

    DUST_SERVICE_URL = IRSA_DUST_SERVER()
    TIMEOUT = IRSA_DUST_TIMEOUT()
    image_type_to_section = {
        'extinction': 't',
        'ebv': 'r',
        '100um': 'e'
    }

    def __init__(self, *args):
        pass

    @class_or_instance
    def get_images(self, coordinate, radius=None,
                   image_type=None, timeout=TIMEOUT, get_query_payload=False):
        """
        A query function that performs a coordinate-based query to acquire Irsa-Dust images

        Parameters
        ----------
        coordinate : str
            Can be either the name of an object or a coordinate string
            If a name, must be resolveable by NED, SIMBAD, 2MASS, or SWAS.
            Examples of acceptable coordinate strings, can be found here:
            http://irsa.ipac.caltech.edu/applications/DUST/docs/coordinate.html.
        radius : str/astropy.units.Quantity, optional
            The size of the region to include in the dust query, in radian, degree
            or hour as per format specified by `astropy.coordinates.Angle or `astropy
            .units.Quantity`. Defaults to 5 degrees.
        image_type : str, optional
            When missing returns for all the images. Otherwise returns only
            for image of the specified type which must be one of `extinction`, `ebv`,
            `100um`. Defaults to `None`.
        timeout : int, optional
            Time limit for establishing successful connection with remote server.
            Defaults to `astroquery.irsa_dust.IrsaDust.TIMEOUT`.
        get_query_payload : bool, optional
            If true than returns the dictionary of query parameters, posted to
            remote server. Defaults to `False`.

        Returns
        -------
        A list of `astropy.fits.HDUList` objects

        """

        if get_query_payload:
            return self._args_to_payload(coordinate, radius=radius)
        readable_objs = self.get_images_async(
            coordinate, radius=radius, image_type=image_type,
            timeout=timeout, get_query_payload=get_query_payload)
        return [fits.open(obj.__enter__()) for obj in readable_objs]

    @class_or_instance
    def get_images_async(self, coordinate, radius=None,
                         image_type=None, timeout=TIMEOUT, get_query_payload=False):
        """
        A query function similar to `astroquery.irsa_dust.IrsaDust.get_images` but
        returns file-handlers to the remote files rather than downloading them. Useful
        for asynchronous queries so that the actual download may be performed later.

        Parameters
        ----------
        coordinate : str
            Can be either the name of an object or a coordinate string
            If a name, must be resolveable by NED, SIMBAD, 2MASS, or SWAS.
            Examples of acceptable coordinate strings, can be found here:
            http://irsa.ipac.caltech.edu/applications/DUST/docs/coordinate.html
        radius : str/astropy.units.Quantity, optional
            The size of the region to include in the dust query, in radian, degree
            or hour as per format specified by `astropy.coordinates.Angle or `astropy
            .units.Quantity`. Defaults to 5 degrees.
        image_type : str, optional
            When missing returns for all the images. Otherwise returns only
            for image of the specified type which must be one of `extinction`, `ebv`,
            `100um`. Defaults to `None`.
        timeout : int, optional
            Time limit for establishing successful connection with remote server.
            Defaults to `astroquery.irsa_dust.IrsaDust.TIMEOUT`
        get_query_payload : bool, optional
            If true than returns the dictionary of query parameters, posted to
            remote server. Defaults to `False`

        Returns
        --------
        A list of context-managers that yield readable file-like objects
        """

        if get_query_payload:
            return self._args_to_payload(coordinate, radius=radius)
        image_urls = self.get_image_list(coordinate, radius=radius,
                                         image_type=image_type, timeout=timeout)
        return [aud.get_readable_fileobj(U) for U in image_urls]

    @class_or_instance
    def get_image_list(
            self, coordinate, radius=None, image_type=None, timeout=TIMEOUT):
        """
        Query function that performes coordinate-based query and returns a list of
        URLs to the Irsa-Dust images

        Parameters
        -----------
        coordinate : str
            Can be either the name of an object or a coordinate string
            If a name, must be resolveable by NED, SIMBAD, 2MASS, or SWAS.
            Examples of acceptable coordinate strings, can be found here:
            http://irsa.ipac.caltech.edu/applications/DUST/docs/coordinate.html
        radius : str/astropy.units.Quantity, optional
            The size of the region to include in the dust query, in radian, degree
            or hour as per format specified by `astropy.coordinates.Angle or `astropy
            .units.Quantity`. Defaults to 5 degrees.
        image_type : str, optional
            When missing returns for all the images. Otherwise returns only
            for image of the specified type which must be one of `extinction`,
            `ebv`, `100um`. Defaults to `None`.
        timeout : int, optional
            Time limit for establishing successful connection with remote server.
            Defaults to `astroquery.irsa_dust.IrsaDust.TIMEOUT`
        get_query_payload : bool
            If true than returns the dictionary of query parameters, posted to
            remote server. Defaults to `False`

        Returns
        --------
        A list of URLs to the FITS images corresponding to the queried object
        """
        url = IrsaDust.DUST_SERVICE_URL
        request_payload = self._args_to_payload(coordinate, radius=radius)
        response = commons.send_request(url, request_payload, timeout)
        return self.extract_image_urls(response.text, image_type=image_type)

    @class_or_instance
    def get_extinction_table(self, coordinate, radius=None, timeout=TIMEOUT):
        """
        Query function that fetches the extinction table from the query
        result

        Parameters
        ----------
        coordinate : str
            Can be either the name of an object or a coordinate string
            If a name, must be resolveable by NED, SIMBAD, 2MASS, or SWAS.
            Examples of acceptable coordinate strings, can be found here:
            http://irsa.ipac.caltech.edu/applications/DUST/docs/coordinate.html
        radius : str/astropy.units.Quantity, optional
            The size of the region to include in the dust query, in radian, degree
            or hour as per format specified by `astropy.coordinates.Angle or `astropy
            .units.Quantity`. Defaults to 5 degrees.
        timeout : int, optional
            Time limit for establishing successful connection with remote server.
            Defaults to `astroquery.irsa_dust.IrsaDust.TIMEOUT`

        Returns
        --------
        table : `astropy.table.Table`
        """
        readable_obj = self.get_extinction_table_async(
            coordinate, radius=radius, timeout=timeout)
        table = Table.read(readable_obj.__enter__(), format='ipac')
        return table

    @class_or_instance
    def get_extinction_table_async(
            self, coordinate, radius=None, timeout=TIMEOUT):
        """
        A query function similar to `astroquery.irsa_dust.IrsaDust.get_extinction_table`
        but returns a file-handler to the remote files rather than downloading it.
        Useful for asynchronous queries so that the actual download may be performed later.

        Parameters
        ----------
        coordinate : str
            Can be either the name of an object or a coordinate string
            If a name, must be resolveable by NED, SIMBAD, 2MASS, or SWAS.
            Examples of acceptable coordinate strings, can be found here:
            http://irsa.ipac.caltech.edu/applications/DUST/docs/coordinate.html
        radius : str, optional
            The size of the region to include in the dust query, in radian, degree
            or hour as per format specified by `astropy.coordinates.Angle`. Defaults
            to 5 degrees.
        timeout : int, optional
            Time limit for establishing successful connection with remote server.
            Defaults to `astroquery.irsa_dust.IrsaDust.TIMEOUT`

        Returns
        -------
        A context manager that yields a file like readable object
        """
        url = IrsaDust.DUST_SERVICE_URL
        request_payload = self._args_to_payload(coordinate, radius=radius)
        response = commons.send_request(url, request_payload, timeout)
        xml_tree = utils.xml(response.text)
        result = SingleDustResult(xml_tree, coordinate)
        return aud.get_readable_fileobj(result.ext_detail_table())

    @class_or_instance
    def get_query_table(self, coordinate, radius=None,
                        section=None, timeout=TIMEOUT, url=DUST_SERVICE_URL):
        """
        Create and return an astropy Table representing the query response(s).
        When `section` is missing, returns the full table. When a
        section is specified (`location`, `extinction`, `ebv`, or `100um`),
        only that portion of the table is returned.

        Parameters
        ----------
        coordinate : str
            Can be either the name of an object or a coordinate string
            If a name, must be resolveable by NED, SIMBAD, 2MASS, or SWAS.
            Examples of acceptable coordinate strings, can be found here:
            http://irsa.ipac.caltech.edu/applications/DUST/docs/coordinate.html
        radius : str/astropy.units.Quantity, optional
            The size of the region to include in the dust query, in radian, degree
            or hour as per format specified by `astropy.coordinates.Angle or `astropy
            .units.Quantity`. Defaults to 5 degrees.
        section : str, optional
            When missing, all the sections of the query result are returned.
            Otherwise only the specified section (`ebv`, `100um`, extinction`,
            `location`) is returned. Defaults to `None`
        timeout : int, optional
            Time limit for establishing successful connection with remote server.
            Defaults to `astroquery.irsa_dust.IrsaDust.TIMEOUT`
        url : str, optional
            Only provided for debugging. Should generally not be assigned.
            Defaults to `astroquery.irsa_dust.IrsaDust.DUST_SERVICE_URL`

        Returns
        --------
        table : `astropy.table.Table`
            table representing the query results, (all or as per  specified)
        """
        request_payload = self._args_to_payload(coordinate, radius=radius)
        response = commons.send_request(url, request_payload, timeout)
        xml_tree = utils.xml(response.text)
        result = SingleDustResult(xml_tree, coordinate)
        if section is None or section in ["location", "loc", "l"]:
            return result.table(section=section)
        try:
            section = IrsaDust.image_type_to_section[section]
            return result.table(section=section)
        except KeyError:
            msg = ('section must be one of the following:\n'
                   'ebv, extinction, location or 100um.')
            raise ValueError(msg)

    @class_or_instance
    def _args_to_payload(self, coordinate, radius=None):
        """
        Accepts the query parameters and returns a dictionary
        suitable to be sent as data via a HTTP POST request

        Parameters
        ----------
        coordinate : str
            Can be either the name of an object or a coordinate string
            If a name, must be resolveable by NED, SIMBAD, 2MASS, or SWAS.
            Examples of acceptable coordinate strings, can be found here:
            http://irsa.ipac.caltech.edu/applications/DUST/docs/coordinate.html
        radius : str/astropy.units.Quantity, optional
            The size of the region to include in the dust query, in radian, degree
            or hour as per format specified by `astropy.coordinates.Angle or `astropy
            .units.Quantity`. Defaults to 5 degrees.

        Returns
        -------
        payload : dict
            A dictionary that specifies the data for an HTTP POST request
        """
        payload = {"locstr": coordinate}  # check if this is resolvable?
        # check if radius is given with proper units
        if radius is not None:
            try:
                reg_size = commons.radius_to_unit(radius,'degree')
            # astropy v0.2.x throws UnitsError and v>0.2.x throws
            # UnitsException
            except (u.UnitsException, coord.errors.UnitsError, AttributeError):
                raise Exception("Radius not specified with proper unit.")
            # check if radius falls in the acceptable range
            if reg_size < 2 or reg_size > 37.5:
                raise ValueError("Radius (in any unit) must be in the"
                                 " range of 2.0 to 37.5 degrees")
            payload["regSize"] = reg_size
        return payload

    @class_or_instance
    def extract_image_urls(self, raw_xml, image_type=None):
        """
        Extracts the image URLs from the query results and
        returns these as a list. If section is missing or
        `all` returns all the URLs, otherwise returns URL
        corresponding to the section specified (`emission`,
        `reddening`, `temperature`).

        Parameters
        ----------
        raw_xml : str
            XML response returned by the query as a string
        image_type : str, optional
            When missing returns for all the images. Otherwise returns only
            for image of the specified type which must be one of `extinction`, `ebv`,
            `100um`. Defaults to `None`.

        Returns
        -------
        url_list : list
            list of URLs to images extracted from query results.
        """
        # get the xml tree from the response
        xml_tree = utils.xml(raw_xml)
        result = SingleDustResult(xml_tree)
        if image_type is None:
            url_list = [result.image(sec) for sec in
                        ['r', 'e', 't']]
        else:
            try:
                section = IrsaDust.image_type_to_section[image_type]
                url_list = [result.image(section)]
            except KeyError:
                msg = ('image_type must be one of the following:\n'
                       'ebv, extinction or 100um.')
                raise ValueError(msg)
        return url_list

    @class_or_instance
    def list_image_types(self):
        """
        Returns a list of image_types available in the Irsa Dust
        query results
        """
        return [key for key in IrsaDust.image_type_to_section]


class SingleDustResult(object):

    """
    Represents the response to a dust query for a single object or location.
    Provides methods to return the response as an astropy Table, and to retrieve
    FITS images listed as urls in the initial response. It can also retrieve
    a detailed extinction table linked to in the initial response. Not intended
    to be instantiated by the end user.
    """

    def __init__(self, xml_tree, query_loc=None):
        """
        Parameters
        ----------
        xml_root : `xml.etree.ElementTree`
            the xml tree representing the response to the query
        query_loc : str
            the location string specified in the query
        """
        self._xml = xml_tree
        self._query_loc = query_loc

        self._location_section = LocationSection(xml_tree)

        ext_node = utils.find_result_node(EXT_DESC, xml_tree)
        self._ext_section = ExtinctionSection(ext_node)

        em_node = utils.find_result_node(EM_DESC, xml_tree)
        self._em_section = EmissionSection(em_node)

        temp_node = utils.find_result_node(TEMP_DESC, xml_tree)
        self._temp_section = TemperatureSection(temp_node)

        self._result_sections = [self._location_section, self._ext_section,
                                 self._em_section, self._temp_section]

    @property
    def query_loc(self):
        """Return the location string used in the query."""
        return self._query_loc

    @property
    def xml(self):
        """Return the raw xml underlying this SingleDustResult."""
        return self._xml

    def table(self, section=None):
        """
        Create and return an astropy Table representing the query response.

        Parameters
        ----------
        section : str
            (optional) the name of the section to include in the table.
            If not provided, the entire table will be returned.
        """
        code = self._section_code(section)
        if code == "all":
            return self._table_all()
        else:
            return self._table(code)

    def values(self, section=None):
        """
        Return the data values contained in the query response,
        i.e. the list of values corresponding to a row in the result table.

        Parameters
        ----------
        section : str
            the name of the section to include in the response
            If no section is given, all sections will be included.
        """
        code = self._section_code(section)
        sections = self._sections(code)

        values = []
        for sec in sections:
            values.extend(sec.values())
        return values

    def _section_code(self, section):
        """
        Return a one-letter code identifying the section.

        Parameters
        ----------
        section : str
            the name or abbreviated name of the section

        Returns
        -------
            str: a one-letter code identifying the section.
        """
        if section is None or section == "all":
            return "all"
        else:
            if section in ["location", "loc", "l"]:
                return "l"
            elif section in ["reddening", "red", "r"]:
                return "r"
            elif section in ["emission", "em", "e"]:
                return "e"
            elif section in ["temperature", "temp", "t"]:
                return "t"
            else:
                msg = """section must be one of the following:
                        'all',
                        'location', 'loc', 'l',
                        'reddening', 'red', 'r',
                        'emission', 'em', 'e',
                        'temperature', 'temp', 't'."""
                raise ValueError(msg)

    def _sections(self, code):
        """
        Parameters
        ----------
        code : str
            the one-letter code name of the section

        Returns
        -------
        The section corresponding to the code, or a list containing all sections if
        no section is provided.
        """
        if code == 'l':
            return [self._location_section]
        elif code == 'r':
            return [self._ext_section]
        elif code == 'e':
            return [self._em_section]
        elif code == 't':
            return [self._temp_section]
        return [self._location_section, self._ext_section, self._em_section, self._temp_section]

    def _table_all(self):
        """
        Create and return the full table containing all four sections:
        location, extinction, emission, and temperature.

        Returns
        -------
        table : `astropy.table.Table`
            table containing the data from the query response
        """
        columns = (self._location_section.columns + self._ext_section.columns
                   + self._em_section.columns + self._temp_section.columns)
        table = Table(data=columns)

        values = self.values()
        table.add_row(vals=values)
        return table

    def _table(self, section):
        """
        Create and return a smaller table containing only one section
        of the overall DustResult table.

        Parameters
        ----------
        section : str
            a string indicating the section to be returned
        """
        # Get the specified section
        section_object = self._sections(section)[0]

        # Create the table
        columns = section_object.columns
        table = Table(data=columns)

        # Populate the table
        values = section_object.values()
        table.add_row(vals=values)

        return table

    def ext_detail_table(self):
        """
        Get the url of the additional, detailed table of extinction data for various filters.
        There is a url for this table given in the initial response to the query.

        Returns
        -------
        table_url : str
            url of the detailed table of extinction data by filter
        """
        table_url = self._ext_section.table_url
        # response = utils.ext_detail_table(table_url)
        # if sys.version_info > (3, 0):
        #   read_response = response.read().decode("utf-8")
        # else:
        #   read_response = response.read()
        # table = Table.read(read_response, format="ipac")
        # return table
        return table_url

    def image(self, section):
        """
        Get the FITS image url associated with the given section.
        The extinction, emission, and temperature sections each provide
        a url to a FITS image.

        Parameters
        ----------
        section : str
            the name of the section

        Returns
        -------
        url : str
            the url to the FITS image
        """
        # Get the url of the image for the given section
        image_url = None
        if section in ["reddening", "red", "r"]:
            image_url = self._ext_section.image_url
        elif section in ["emission", "em", "e"]:
            image_url = self._em_section.image_url
        elif section in ["temperature", "temp", "t"]:
            image_url = self._temp_section.image_url

        if image_url is None:
            msg = """section must be one of the following values:
                    'reddening', 'red', 'r',
                    'emission', 'em', 'e',
                    'temperature', 'temp', 't'"""
            raise ValueError(msg)

        # response = utils.image(image_url)

        # S = io.BytesIO(response)
        # image = fits.open(S)
        return image_url

    def __str__(self):
        """Return a string representation of the table."""
        string = "[DustResult: \n\t"
        for section in self._result_sections:
            if len(string) > 15:
                string += ",\n\t"
            string += section.__str__()
        string += "]"
        return string


class BaseDustNode(object):

    """
    A node in the result xml that has been enhanced to return values and Columns
    appropriate to its type (String, Number, or Coord).
    """

    def __init__(self, xml_node):
        """
        Parameters
        ----------
        xml_node : `xml.etree.ElementTree`
            the xml node that provides the raw data for this DustNode
        """
        self._name = xml_node.tag

    def set_value(self, node_text):
        """Override in subclasses."""
        pass

    @property
    def name(self):
        """Return the xml node name."""
        return self._name

    @property
    def value(self):
        """Return the value extracted from the node."""
        return self._value

    @property
    def columns(self):
        """Return the column or columns associated with this item in the astropy Table."""
        return self._columns

    def __str__(self):
        """Return a string representation of this item."""
        col_str = "[Column: "
        for column in self._columns:
            for format_str in column.pformat(show_units=True):
                col_str += format_str
        string = "name: " + self._name + ", " + col_str + "]"
        return string


class StringNode(BaseDustNode):

    """
    A node that contains text.
    """

    def __init__(self, xml_node, col_name, length):
        """
        Parameters
        ----------
        xml_node : `xml.etree.ElementTree`
            the xml node that provides the raw data for this DustNode
        col_name : str
            the name of the column associated with this item
        length : int
            the size of the column associated with this item
        """
        BaseDustNode.__init__(self, xml_node)

        self._value = xml_node.text.strip()

        self._length = length
        self._columns = [Column(name=col_name, dtype="S" + str(length))]

    def __str__(self):
        """Return a string representation of this item."""
        base_string = BaseDustNode.__str__(self)
        string = ("[StringNode: " + base_string
                  + ", value: " + self._value + "]")
        return string


class NumberNode(BaseDustNode):

    """
    A node that contains a number. Outputs a single column containing the number.
    """

    def __init__(self, xml_node, col_name, units=None):
        """
        Parameters
        ----------
        xml_node : `xml.etree.ElementTree`
            the xml node that provides the raw data for this DustNode
        col_name : str
            the name of the column associated with this item
        units : `astropy.units.Unit`
            the units associated with this item
        """
        BaseDustNode.__init__(self, xml_node)
        self._value = utils.parse_number(xml_node.text)
        self._columns = [Column(name=col_name, units=units)]

    def __str__(self):
        """Return a string representation of the item."""
        base_string = BaseDustNode.__str__(self)

        string = ("[NumberNode: " + base_string
                  + ", value: " + str(self._value) + "]")
        return string


class CoordNode(BaseDustNode):

    """
    A node that contains RA, Dec coordinates. Outputs three values / columns: RA, Dec
    and a coordinate system description string.
    """

    def __init__(self, xml_node, col_names):
        """
        Parameters
        ----------
        xml_node : `xml.etree.ElementTree`
            the xml node that provides the raw data for this DustNode
        col_names : str
            the names of the columns associated with this item
        """
        BaseDustNode.__init__(self, xml_node)
        self._value = utils.parse_coords(xml_node.text)
        units = u.deg
        self._columns = [Column(name=col_names[0], units=units),
                         Column(name=col_names[1], units=units),
                         Column(name=col_names[2], dtype="S25")]

    def __str__(self):
        """Return a string representation of the item."""
        base_string = BaseDustNode.__str__(self)
        values_str = ("values: " + str(self._value[0]) + ", " + str(self._value[1])
                      + ", " + str(self._value[2]))
        string = ("[CoordNode: " + base_string + ", " + values_str + "]")
        return string


class BaseResultSection(object):

    """
    Represents a group of related nodes/columns in a DustResults object.
    A DustResults table contains four main sections:
        1-location
        2-extinction
        3-emission
        4-temperature
    In addition, the extinction, emission, and temperature sections
    each contain a nested statistics subsection.
    """

    def node_dict(self, names, xml_root):
        """
        Find all the nodes with the given names under the given root,
        and put them in a dictionary.

        Parameters
        ----------
        names : list[str]
            the names of the nodes to find
        xml_root : `xml.etree.ElementTree`
            the root of the xml tree to search

        Returns
        -------
        nodes : dictionary
            a dictionary of xml nodes, where the keys are the node names
        """
        nodes = {}
        for name in names:
            found_node = xml_root.find(name)
            if found_node is None:
                raise ValueError("Could not find node '" + name + "'")
            nodes[name] = found_node
        return nodes

    def create_columns(self):
        """Build the columns associated with this section."""
        columns = []
        for dust_node in self._dust_nodes:
            if isinstance(dust_node._columns, list):
                columns.extend(dust_node._columns)
            else:
                columns.append(dust_node._columns)
        self._columns = columns

    @property
    def columns(self):
        """Return the list of columns associated with this section."""
        return self._columns

    def values(self):
        """Return the list of data values associated with this section,
        i.e. the data corresponding to a single row in the results table."""
        values = []
        for dust_node in self._dust_nodes:
            if isinstance(dust_node._value, list):
                values.extend(dust_node._value)
            else:
                values.append(dust_node._value)
        return values

    def __str__(self):
        """Return a string representation of the section."""
        string = "\n\t\t"
        for dust_node in self._dust_nodes:
            if len(string) > 6:
                string += ",\n\t\t"
            string += dust_node.__str__()
        return string


class LocationSection(BaseResultSection):

    """
    The location section of the DustResults object.
    """

    def __init__(self, xml_root):
        """
        Parameters
        ----------
        xml_root : `xml.etree.ElementTree`
            the xml tree where the data for this section resides
        """
        location_node = xml_root.find(INPUT)
        names = [OBJ_NAME, REG_SIZE]
        xml_nodes = self.node_dict(names, location_node)

        # Create the section's DustNodes
        self._dust_nodes = [CoordNode(
            xml_nodes[OBJ_NAME], col_names=["RA", "Dec", "coord sys"]),
            NumberNode(xml_nodes[REG_SIZE], REG_SIZE, u.deg)]

        self.create_columns()

    def __str__(self):
        """Return a string representation of the section."""
        base_string = BaseResultSection.__str__(self)
        string = "[LocationSection: " + base_string + "]"
        return string


class StatsSection(BaseResultSection):

    """
    The statistics subsection of one of an extinction, emission, or temperature
    section.
    """

    def __init__(self, xml_root, col_prefix):
        """
        Parameters
        ----------
        xml_root : `xml.etree.ElementTree`
            The xml tree containing the data for this section
        col_prefix : str
            the prefix to use in column names for this section
        """
        names = [
            REF_PIXEL_VALUE,
            REF_COORDINATE,
            MEAN_VALUE,
            STD,
            MAX_VALUE,
            MIN_VALUE]
        xml_nodes = self.node_dict(names, xml_root)

        # Create the DustNodes
        self._dust_nodes = [NumberNode(
            xml_nodes[REF_PIXEL_VALUE], col_prefix + " ref"),
            CoordNode(
                xml_nodes[
                    REF_COORDINATE], col_names=[col_prefix + " ref RA",
                                                col_prefix + " ref Dec", col_prefix + " ref coord sys"]),
            NumberNode(
                xml_nodes[
                    MEAN_VALUE],
                col_prefix +
                " mean"),
            NumberNode(xml_nodes[STD], col_prefix + " std"),
            NumberNode(xml_nodes[MAX_VALUE], col_prefix + " max"),
            NumberNode(xml_nodes[MIN_VALUE], col_prefix + " min")]

        self._units = utils.parse_units(xml_nodes[REF_PIXEL_VALUE].text)

        self.create_columns()

    @property
    def units(self):
        """Return the units associated with this section."""
        return self._units

    @property
    def dust_nodes(self):
        """Return the list of DustNodes in this section."""
        return self._dust_nodes

    def __str__(self):
        """Return a string representation of the section."""
        base_string = "\n\t\t\t\t"
        for dust_node in self._dust_nodes:
            if len(base_string) > 6:
                base_string += ",\n\t\t\t\t"
            base_string += dust_node.__str__()
        string = "\n\t\t\t[StatisticsSection: " + base_string + "]"
        return string


class ExtinctionSection(BaseResultSection):

    """
    The extinction (reddening) section in a DustResults object.
    """

    def __init__(self, xml_root):
        """
        Parameters
        ----------
        xml_root : `xml.etree.ElementTree`
            The xml tree containing the data for this section
        """
        # Find the section's xml nodes
        names = [DESC, DATA_IMAGE, DATA_TABLE, STATISTICS]
        xml_nodes = self.node_dict(names, xml_root)

        # Build the DustNodes
        self._dust_nodes = [StringNode(xml_nodes[DESC], "ext desc", 100),
                            StringNode(
                            xml_nodes[
                            DATA_IMAGE],
                            "ext image",
                            255),
                            StringNode(xml_nodes[DATA_TABLE], "ext table", 255)]

        # Create statistics subsection
        self._stats = StatsSection(xml_nodes[STATISTICS], "ext")

        self.create_columns()

    def create_columns(self):
        """Build the columns associated with this section."""
        BaseResultSection.create_columns(self)
        self._columns.extend(self._stats.columns)

    @property
    def table_url(self):
        """Return the url where the extinction detail table can be found."""
        table_url = self._dust_nodes[2]._value
        return table_url

    @property
    def image_url(self):
        """Return the url of the FITS image associated with this section."""
        return self._dust_nodes[1]._value

    def values(self):
        """Return the data values associated with this section,
        i.e. the list of values corresponding to a single row in the results table."""
        ext_values = BaseResultSection.values(self)
        ext_values.extend(self._stats.values())
        return ext_values

    def __str__(self):
        """Return a string representation of the section."""
        base_string = BaseResultSection.__str__(self)
        string = "[ExtinctionSection: " + \
            base_string + self._stats.__str__() + "]"
        return string


class EmissionSection(BaseResultSection):

    """
    The emission section in a DustResults object.
    """

    def __init__(self, xml_root):
        """
        Parameters
        ----------
        xml_root : `xml.etree.ElementTree`
            The xml tree containing the data for this section
        """
        names = [DESC, DATA_IMAGE, STATISTICS]
        xml_nodes = self.node_dict(names, xml_root)

        # Create the DustNodes
        self._dust_nodes = [StringNode(xml_nodes[DESC], "em desc", 100),
                            StringNode(xml_nodes[DATA_IMAGE], "em image", 255)]

        # Create the statistics subsection
        self._stats = StatsSection(xml_nodes[STATISTICS], "em")

        self.create_columns()

    def create_columns(self):
        """Build the columns associated with this section."""
        BaseResultSection.create_columns(self)
        self._columns.extend(self._stats.columns)

    def values(self):
        """Return the data values associated with this section,
        i.e. the list of values corresponding to a single row in the results table."""
        values = BaseResultSection.values(self)
        values.extend(self._stats.values())
        return values

    @property
    def image_url(self):
        """Return the url of the FITS image associated with this section."""
        return self._dust_nodes[1]._value

    def __str__(self):
        """Return a string representation of the section."""
        base_string = BaseResultSection.__str__(self)
        string = "[EmissionSection: " + \
            base_string + self._stats.__str__() + "]"
        return string


class TemperatureSection(BaseResultSection):

    """
    The temperature section in a DustResults object.
    """

    def __init__(self, xml_root):
        """
        Parameters
        ----------
        xml_root : `xml.etree.ElementTree`
            The xml tree containing the data for this section
        """
        names = [DESC, DATA_IMAGE, STATISTICS]
        xml_nodes = self.node_dict(names, xml_root)

        # Create the DustNodes
        self._dust_nodes = [StringNode(xml_nodes[DESC], "temp desc", 100),
                            StringNode(xml_nodes[DATA_IMAGE], "temp image", 255)]

        # Create the statistics subsection
        self._stats = StatsSection(xml_nodes[STATISTICS], "temp")

        self.create_columns()

    def create_columns(self):
        """Build the columns associated with this section."""
        BaseResultSection.create_columns(self)
        self._columns.extend(self._stats.columns)

    def values(self):
        """Return the data values associated with this section,
        i.e. the list of values corresponding to a single row in the results table."""
        values = BaseResultSection.values(self)
        values.extend(self._stats.values())
        return values

    @property
    def image_url(self):
        """Return the url of the FITS image associated with this section."""
        return self._dust_nodes[1]._value

    def __str__(self):
        """Return a string representation of the section."""
        base_string = BaseResultSection.__str__(self)
        string = "[TemperatureSection: " + \
            base_string + self._stats.__str__() + "]"
        return string
