# Licensed under a 3-clause BSD style license - see LICENSE.rst
import urllib2
import requests
import astropy.coordinates as coord
import astropy.units as u
from ...utils import chunk_read, chunk_report
from ...utils import class_or_instance
from ...utils import commons
from ...utils.process_asyncs import async_to_sync_docstr,async_to_sync
from ...utils.docstr_chompers import remove_returns,prepend_docstr_noreturns
from astropy.table import Table
from astropy.tests.helper import pytest, remote_data
import astropy.io.votable as votable
import textwrap
from numpy import testing as npt
from astropy.utils import OrderedDict

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
def test_utils():
    response = urllib2.urlopen('http://www.ebay.com')
    C = chunk_read(response, report_hook=chunk_report)
    print(C)


def test_class_or_instance():
    assert SimpleQueryClass.query() == "class"
    U = SimpleQueryClass()
    assert U.query() == "instance"
    assert SimpleQueryClass.query.__doc__ == " docstring "


@pytest.mark.parametrize(('coordinates'),
                         [coord.ICRSCoordinates(ra=148,
                                                dec=69,
                                                unit=(u.deg, u.deg)),
                          ])
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


@pytest.mark.parametrize(('radius'),
                         ['5d0m0s',
                          5 * u.deg
                          ])
def test_parse_radius_1(radius):
    assert commons.radius_to_unit(radius,'degree') == 5


# this test fails to fail appropriately, apparently...
# I get a "DID NOT RAISE" failure running locally,
# even though every interactive test I have tried DOES
# raise an exception.
@pytest.mark.parametrize(('radius'),
                         [5,
                          #9.8 * u.kg
                          ])
def test_parse_radius_2(radius):
    with pytest.raises(Exception):
        commons.parse_radius(radius)

@pytest.mark.parametrize(('inv','inunit','outv','outunit'),
                         zip((1,5,1,5,66,3960),
                             ('deg','degree','deg','deg','arcmin','arcsec'),
                             (1,5,60,18000,1.1,1.1),
                             ('deg',u.deg,'arcmin','arcsec','deg','deg')))
def test_radius_to_unit(inv,inunit,outv,outunit):
    x = inv*u.Unit(inunit)
    npt.assert_almost_equal(commons.radius_to_unit(x, outunit), outv)

def test_send_request_post(monkeypatch):
    def mock_post(url, data, timeout, headers={}):
        class SpecialMockResponse(object):

            def __init__(self, url, data, headers):
                self.url = url
                self.data = data
                self.headers = headers
        return SpecialMockResponse(url, data, headers=headers)
    monkeypatch.setattr(requests, 'post', mock_post)

    response = commons.send_request('https://github.com/astropy/astroquery',
                                    data=dict(msg='ok'), timeout=30)
    assert response.url == 'https://github.com/astropy/astroquery'
    assert response.data == dict(msg='ok')
    assert 'astroquery' in response.headers['User-Agent']


def test_send_request_get(monkeypatch):
    def mock_get(url, params, timeout, headers={}):
        req = requests.Request('GET', url, params=params, headers=headers).prepare()
        return req
    monkeypatch.setattr(requests, 'get', mock_get)
    response = commons.send_request('https://github.com/astropy/astroquery',
                                    dict(a='b'), 60, request_type='GET')
    assert response.url == 'https://github.com/astropy/astroquery?a=b'


def test_send_request_err():
    with pytest.raises(ValueError):
        commons.send_request('https://github.com/astropy/astroquery',
                             dict(a='b'), 60, request_type='PUT')

col_1 = [1, 2, 3]
col_2 = [0, 1, 0, 1, 0, 1]
col_3 = ['v','w', 'x', 'y', 'z']
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
        An `astropy.table.Table` object
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

        Example
        -------
        >>> from astroquery.vizier import Vizier
        >>> catalog_list = Vizier.find_catalogs('Kang W51')
        >>> print(catalog_list)
        {u'J/ApJ/706/83': <astropy.io.votable.tree.Resource at 0x108d4d490>,
         u'J/ApJS/191/232': <astropy.io.votable.tree.Resource at 0x108d50490>}
        >>> print({k:v.description for k,v in catalog_list.iteritems()})
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

        Example
        -------
        >>> from astroquery.vizier import Vizier
        >>> catalog_list = Vizier.find_catalogs('Kang W51')
        >>> print(catalog_list)
        {u'J/ApJ/706/83': <astropy.io.votable.tree.Resource at 0x108d4d490>,
         u'J/ApJS/191/232': <astropy.io.votable.tree.Resource at 0x108d50490>}
        >>> print({k:v.description for k,v in catalog_list.iteritems()})
        {u'J/ApJ/706/83': u'Embedded YSO candidates in W51 (Kang+, 2009)',
         u'J/ApJS/191/232': u'CO survey of W51 molecular cloud (Bieging+, 2010)'}

        Returns
        -------
        A `dict` object
        """)


def test_process_async_docs():
    assert async_to_sync_docstr(docstr1) == docstr1_out
    assert async_to_sync_docstr(docstr2,returntype='dict') == docstr2_out


class Dummy:

    def do_nothing_async():
        """ docstr """
        pass


def test_async_to_sync(cls=Dummy):
    newcls = async_to_sync(Dummy)
    assert hasattr(newcls,"do_nothing")

docstr3 = """
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


def test_return_chomper(doc=docstr3,out=docstr3_out):
    assert remove_returns(doc) == [x.lstrip() for x in out.split('\n')]


def dummyfunc():
    """
    Returns
    -------
    Nothing!

    Examples
    --------
    Nada
    """
    pass

docstr4 = """
    Blah Blah Blah

    Returns
    -------
    nothing
"""

docstr4_out = """
    Blah Blah Blah

    Returns
    -------
    Nothing!

    Examples
    --------
    Nada
"""


def test_prepend_docstr(doc=docstr4,func=dummyfunc,out=docstr4_out):
    fn = prepend_docstr_noreturns(doc)(func)
    assert fn.__doc__ == textwrap.dedent(docstr4_out)


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
    assert isinstance(result, basestring)
