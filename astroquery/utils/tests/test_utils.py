# Licensed under a 3-clause BSD style license - see LICENSE.rst

from collections import OrderedDict
import os
import requests
import pytest
import tempfile
import textwrap

import astropy.coordinates as coord
from astropy.extern.six.moves import urllib
from astropy.extern import six
from astropy.io import fits
import astropy.io.votable as votable
import astropy.units as u
from astropy.table import Table
from astropy.tests.helper import remote_data
import astropy.utils.data as aud

from ...utils import chunk_read, chunk_report, class_or_instance, commons
from ...utils.process_asyncs import async_to_sync_docstr, async_to_sync
from ...utils.docstr_chompers import remove_sections, prepend_docstr_nosections


class SimpleQueryClass(object):

    @class_or_instance
    def query(self):
        """ docstring """
        if self is SimpleQueryClass:
            print("Calling query as class method")
            return "class"
        else:
            print("Calling query as instance method")
            return "instance"


@remote_data
def test_chunk_read():
    datasize = 50000
    response = urllib.request.urlopen('http://httpbin.org/stream-bytes/{0}'.format(datasize))
    C = chunk_read(response, report_hook=chunk_report)
    assert len(C) == datasize


def test_class_or_instance():
    assert SimpleQueryClass.query() == "class"
    U = SimpleQueryClass()
    assert U.query() == "instance"
    assert SimpleQueryClass.query.__doc__ == " docstring "


@pytest.mark.parametrize(('coordinates'),
                         [coord.SkyCoord(ra=148, dec=69, unit=(u.deg, u.deg)),
                          ]
                         )
def test_parse_coordinates_1(coordinates):
    c = commons.parse_coordinates(coordinates)
    assert c is not None


@remote_data
@pytest.mark.parametrize(('coordinates'),
                         ["00h42m44.3s +41d16m9s",
                          "m81"])
def test_parse_coordinates_2(coordinates):
    c = commons.parse_coordinates(coordinates)
    assert c is not None


def test_parse_coordinates_3():
    with pytest.raises(Exception):
        commons.parse_coordinates(9.8 * u.kg)


def test_send_request_post(monkeypatch):
    def mock_post(url, data, timeout, headers={}, status_code=200):
        class SpecialMockResponse(object):

            def __init__(self, url, data, headers, status_code):
                self.url = url
                self.data = data
                self.headers = headers
                self.status_code = status_code

            def raise_for_status(self):
                pass

        return SpecialMockResponse(url, data, headers=headers,
                                   status_code=status_code)
    monkeypatch.setattr(requests, 'post', mock_post)

    response = commons.send_request('https://github.com/astropy/astroquery',
                                    data=dict(msg='ok'), timeout=30)
    assert response.url == 'https://github.com/astropy/astroquery'
    assert response.data == dict(msg='ok')
    assert 'astroquery' in response.headers['User-Agent']


def test_send_request_get(monkeypatch):
    def mock_get(url, params, timeout, headers={}, status_code=200):
        req = requests.Request(
            'GET', url, params=params, headers=headers).prepare()
        req.status_code = status_code
        req.raise_for_status = lambda: None
        return req
    monkeypatch.setattr(requests, 'get', mock_get)
    response = commons.send_request('https://github.com/astropy/astroquery',
                                    dict(a='b'), 60, request_type='GET')
    assert response.url == 'https://github.com/astropy/astroquery?a=b'


def test_quantity_timeout(monkeypatch):
    def mock_get(url, params, timeout, headers={}, status_code=200):
        req = requests.Request(
            'GET', url, params=params, headers=headers).prepare()
        req.status_code = status_code
        req.raise_for_status = lambda: None
        return req
    monkeypatch.setattr(requests, 'get', mock_get)
    response = commons.send_request('https://github.com/astropy/astroquery',
                                    dict(a='b'), 1 * u.min, request_type='GET')
    assert response.url == 'https://github.com/astropy/astroquery?a=b'


def test_send_request_err():
    with pytest.raises(ValueError):
        commons.send_request('https://github.com/astropy/astroquery',
                             dict(a='b'), 60, request_type='PUT')


col_1 = [1, 2, 3]
col_2 = [0, 1, 0, 1, 0, 1]
col_3 = ['v', 'w', 'x', 'y', 'z']
# table t1 with 1 row and 3 cols
t1 = Table([col_1[:1], col_2[:1], col_3[:1]], meta={'name': 't1'})
# table t2 with 3 rows and 1 col
t2 = Table([col_1], meta={'name': 't2'})
# table t3 with 3 cols and 3 rows
t3 = Table([col_1, col_2[:3], col_3[:3]], meta={'name': 't3'})


def test_TableDict():
    in_list = create_in_odict([t1, t2, t3])
    table_list = commons.TableList(in_list)
    repr_str = table_list.__repr__()
    assert repr_str == ("TableList with 3 tables:"
                        "\n\t'0:t1' with 3 column(s) and 1 row(s) "
                        "\n\t'1:t2' with 1 column(s) and 3 row(s) "
                        "\n\t'2:t3' with 3 column(s) and 3 row(s) ")


def test_TableDict_print_table_list(capsys):
    in_list = create_in_odict([t1, t2, t3])
    table_list = commons.TableList(in_list)
    table_list.print_table_list()
    out, err = capsys.readouterr()
    assert out == ("TableList with 3 tables:"
                   "\n\t'0:t1' with 3 column(s) and 1 row(s) "
                   "\n\t'1:t2' with 1 column(s) and 3 row(s) "
                   "\n\t'2:t3' with 3 column(s) and 3 row(s) \n")


def create_in_odict(t_list):
    return OrderedDict([(t.meta['name'], t) for t in t_list])


def test_suppress_vo_warnings(recwarn):
    commons.suppress_vo_warnings()
    votable.exceptions.warn_or_raise(votable.exceptions.W01)
    votable.exceptions.warn_or_raise(votable.exceptions.VOTableChangeWarning)
    votable.exceptions.warn_or_raise(votable.exceptions.VOWarning)
    votable.exceptions.warn_or_raise(votable.exceptions.VOTableSpecWarning)
    with pytest.raises(Exception):
        recwarn.pop(votable.exceptions.VOWarning)


docstr1 = """
        Query the Vizier service for a specific catalog

        Parameters
        ----------
        catalog : str or list, optional
            The catalog(s) that will be retrieved

        Returns
        -------
        response : `~request.response`
            Returned if asynchronous method used
        result : `~astroquery.utils.common.TableList`
            The results in a list of `astropy.table.Table`.
        """

docstr1_out = textwrap.dedent("""
        Queries the service and returns a table object.

        Query the Vizier service for a specific catalog

        Parameters
        ----------
        catalog : str or list, optional
            The catalog(s) that will be retrieved

        Returns
        -------
        table : A `~astropy.table.Table` object.
        """)

docstr2 = """
        Search Vizier for catalogs based on a set of keywords, e.g. author name

        Parameters
        ----------
        keywords : list or string
            List of keywords, or space-separated set of keywords.
            From `Vizier <http://vizier.u-strasbg.fr/doc/asu-summary.htx>`_:
            "names or words of title of catalog. The words are and'ed, i.e.
            only the catalogues characterized by all the words are selected."

        Returns
        -------
        Dictionary of the "Resource" name and the VOTable resource object.
        "Resources" are generally publications; one publication may contain
        many tables.

        Examples
        --------
        >>> from astroquery.vizier import Vizier
        >>> catalog_list = Vizier.find_catalogs('Kang W51')
        >>> print(catalog_list)
        {u'J/ApJ/706/83': <astropy.io.votable.tree.Resource at 0x108d4d490>,
         u'J/ApJS/191/232': <astropy.io.votable.tree.Resource at 0x108d50490>}
        >>> print({k:v.description for k,v in catalog_list.items()})
        {u'J/ApJ/706/83': u'Embedded YSO candidates in W51 (Kang+, 2009)',
         u'J/ApJS/191/232': u'CO survey of W51 molecular cloud (Bieging+, 2010)'}
        """

# note that the blank line between "Queries..." and "Search..." is necessary
# for sphinx parsing of the docs
docstr2_out = textwrap.dedent("""
        Queries the service and returns a dict object.

        Search Vizier for catalogs based on a set of keywords, e.g. author name

        Parameters
        ----------
        keywords : list or string
            List of keywords, or space-separated set of keywords.
            From `Vizier <http://vizier.u-strasbg.fr/doc/asu-summary.htx>`_:
            "names or words of title of catalog. The words are and'ed, i.e.
            only the catalogues characterized by all the words are selected."

        Examples
        --------
        >>> from astroquery.vizier import Vizier
        >>> catalog_list = Vizier.find_catalogs('Kang W51')
        >>> print(catalog_list)
        {u'J/ApJ/706/83': <astropy.io.votable.tree.Resource at 0x108d4d490>,
         u'J/ApJS/191/232': <astropy.io.votable.tree.Resource at 0x108d50490>}
        >>> print({k:v.description for k,v in catalog_list.items()})
        {u'J/ApJ/706/83': u'Embedded YSO candidates in W51 (Kang+, 2009)',
         u'J/ApJS/191/232': u'CO survey of W51 molecular cloud (Bieging+, 2010)'}

        Returns
        -------
        dict : A `dict` object.
        """)


def test_process_async_docs():
    assert async_to_sync_docstr(docstr1) == docstr1_out
    assert async_to_sync_docstr(docstr2, returntype='dict') == docstr2_out


class Dummy:

    def do_nothing_async(self):
        """ docstr """
        pass


def test_async_to_sync(cls=Dummy):
    newcls = async_to_sync(Dummy)
    assert hasattr(newcls, "do_nothing")


docstr3 = """
    Parameters
    ----------
    first_param

    Returns
    -------
    Nothing!

    Examples
    --------
    Nada
"""

docstr3_out = """
    Examples
    --------
    Nada
"""


def test_return_chomper(doc=docstr3, out=docstr3_out):
    assert (remove_sections(doc, sections=['Returns', 'Parameters']) ==
            [x.lstrip() for x in out.split('\n')])


def dummyfunc1():
    """
    Returns
    -------
    Nothing!

    Examples
    --------
    Nada
    """
    pass


def dummyfunc2():
    """
    Returns
    -------
    Nothing!
    """
    pass


docstr4 = """
    Blah Blah Blah

    Returns
    -------
    nothing

    Examples
    --------
    no_examples_at_all
"""

docstr4_out1 = """
    Blah Blah Blah

    Returns
    -------
    Nothing!

    Examples
    --------
    Nada
"""

docstr4_out2 = """
    Blah Blah Blah

    Returns
    -------
    Nothing!
"""


@pytest.mark.parametrize("func, out", [(dummyfunc1, docstr4_out1),
                                       (dummyfunc2, docstr4_out2)])
def test_prepend_docstr(func, out, doc=docstr4):
    fn = prepend_docstr_nosections(doc, sections=['Returns', 'Examples'])(func)
    assert fn.__doc__ == textwrap.dedent(out)


@async_to_sync
class DummyQuery(object):

    @class_or_instance
    def query_async(self, *args, **kwargs):
        """ docstr"""
        if kwargs['get_query_payload']:
            return dict(msg='payload returned')
        return 'needs to be parsed'

    @class_or_instance
    def _parse_result(self, response, verbose=False):
        return response


def test_payload_return(cls=DummyQuery):
    result = DummyQuery.query(get_query_payload=True)
    assert isinstance(result, dict)
    result = DummyQuery.query(get_query_payload=False)
    assert isinstance(result, six.string_types)


fitsfilepath = os.path.join(os.path.dirname(__file__),
                            '../../sdss/tests/data/emptyfile.fits')


@pytest.fixture
def patch_getreadablefileobj(request):
    # Monkeypatch hack: ALWAYS treat as a URL
    _is_url = aud._is_url
    aud._is_url = lambda x: True
    _urlopen = urllib.request.urlopen
    filesize = os.path.getsize(fitsfilepath)

    class MockRemote(object):
        def __init__(self, fn, *args, **kwargs):
            self.file = open(fn, 'rb')

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            self.close()

        def info(self):
            return {'Content-Length': filesize}

        def read(self, *args):
            return self.file.read(*args)

        def close(self):
            self.file.close()

    def monkey_urlopen(x, *args, **kwargs):
        print("Monkeyed URLopen")
        return MockRemote(fitsfilepath, *args, **kwargs)

    aud.urllib.request.urlopen = monkey_urlopen
    urllib.request.urlopen = monkey_urlopen

    def closing():
        aud._is_url = _is_url
        urllib.request.urlopen = _urlopen
        aud.urllib.request.urlopen = _urlopen

    request.addfinalizer(closing)


def test_filecontainer_save(patch_getreadablefileobj):
    ffile = commons.FileContainer(fitsfilepath, encoding='binary')
    temp_dir = tempfile.mkdtemp()
    empty_temp_file = temp_dir + os.sep + 'test_emptyfile.fits'
    ffile.save_fits(empty_temp_file)
    assert os.path.exists(empty_temp_file)


def test_filecontainer_get(patch_getreadablefileobj):
    ffile = commons.FileContainer(fitsfilepath, encoding='binary')
    ff = ffile.get_fits()
    assert isinstance(ff, fits.HDUList)


@pytest.mark.parametrize(('coordinates', 'expected'),
                         [("5h0m0s 0d0m0s", True),
                          ("m1", False)
                          ])
def test_is_coordinate(coordinates, expected):
    out = commons._is_coordinate(coordinates)
    assert out == expected
