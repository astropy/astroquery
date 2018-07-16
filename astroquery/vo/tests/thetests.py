import json, os
from astropy.io import ascii
## Why can't I import astroquery.vo ?
from astroquery.vo import Registry

##
##  Regenerate the output JSON files using:
##
##  astroquery/vo > python tests/thetests.py



def table2ecsv(current, filename):
    """Dump a table and its meta data to ECSV"""
    from astropy.io import ascii
    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'data'))
    try:
        ascii.write(current, filename, format='ecsv')
    except Exception as e:
        raise e


def ecsv2table(filename):
    """Read in the previously saved results from JSON and return an astropy Table.

    Reads both the serialized table JSON and the meta data, then combines."""
    from astropy.table import Table
    from astropy.io import ascii
    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'data'))
    print("DEBUGGING:  filename={}".format(filename))
    try:
        with open(filename, 'r') as f:
           table=Table.read(f.read(),format='ascii.ecsv')
    except Exception as e:
        raise
    return table


'''
def table2json(current, filename):
    """Dump a table and its meta data to JSON"""
    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'data'))
    outdict = {'table': current.to_pandas().to_json(), 'meta': current.meta}
    try:
        with open(filename, 'w') as f:
            json.dump(outdict, f, indent=2)
    except Exception as e:
        raise e


def json2table(filename):
    """Read in the previously saved results from JSON and return an astropy Table.

    Reads both the serialized table JSON and the meta data, then combines."""
    from astropy.table import Table
    import pandas as pd
    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'data'))
    try:
        with open(filename, 'r') as f:
            indict = json.load(f)
            table = Table.from_pandas(pd.read_json(indict['table']))
            meta = indict['meta']
    except Exception as e:
        raise
    table.meta = meta
    return table
'''


def raw2json(response, filename):
    """Dump the raw response and things used in meta data like url"""
    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'data'))
    dict = {'astroquery.vo': {'url': response.url, 'text': str(response.content, 'utf-8')}}
    myjson = json.dumps(dict)
    try:
        with open(filename, 'w') as f:
            json.dump(myjson, f, indent=4)
    except Exception as e:
        raise e


def json2raw(filename):
    import requests
    try:
        with open(filename, 'r') as f:
            x = json.loads(json.load(f))['astroquery.vo']
            return x['url'], str.encode(x['text'])
    except Exception as e:
        raise e


def data_path(filename, reinit=False):
    """ In case these paths change depending on test methods?"""
    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'data'))
    return os.path.join(data_dir, filename)


def table_comp(current, filename):
    """Compare the resulting Tables piece by piece

    Trying to give more info than just a failed assertion.
    """
    reference = ecsv2table(filename)
    #reference = json2table(filename)
    table_meta_comp(current, reference)
    table_stats_comp(current, reference)

    return True


def table_meta_comp(current, reference):
    """Check the meta data in the "astroquery.vo" area"""
    assert set(current.meta['astroquery.vo']) == set(reference.meta['astroquery.vo']), "Keys differ:  current={},\n          reference={}".format(current.meta['astroquery.vo'].keys(), reference.meta['astroquery.vo'].keys())
    ## Check their values
    for k in current.meta['astroquery.vo'].keys():
        if "text" in k: continue
        # assert current.meta['astroquery.vo'][k] == reference.meta['astroquery.vo'][k], "Run 'python tests/thetests.py' to generate new outputs and 'git diff tests/data/{}.to_json'".format(DATA_FILES['query_basic'])
        assert current.meta['astroquery.vo'][k] == reference.meta['astroquery.vo'][k], "The value of key {} differs:\ncurrent={},\nreference={}".format(k, current.meta['astroquery.vo'][k], reference.meta['astroquery.vo'][k])
    return True


def table_stats_comp(current, reference):
    """Check some basic properties of the tables like length and columns."""
    assert len(current) >= len(reference), "Current results have {} rows compared to reference with {}".format(len(current), len(reference))
    for col in reference.colnames:
        assert col in current.colnames, "Column {} missing from current result.".format(col)
    return True


## Keep the tests in one place. Import and decorate or init differently in
## test_registry.py or test_registry_remote.py or this main
class TestReg(object):

    DATA_FILES = {'query_basic_response': 'registry_query_basic_response.json',
                  'query_counts_response': 'registry_query_counts_response.json',
                  'query_basic_result': 'registry_query_basic_result.ecsv',
                  "query_counts_result": "registry_query_counts_result.ecsv",
                  'adql_service': 'registry_adql_service.json',
                  "adql_keyword": "registry_adql_keyword.json",
                  "adql_waveband": "registry_adql_waveband.json",
                  "adql_source": "registry_adql_source.json",
                  "adql_publisher": "registry_adql_publisher.json",
                  "adql_orderby": "registry_adql_orderby.json"}

    def rewrite(self):
        """Called by main below to re-generate the reference files."""
        print("DEBUGGING: calling basic(True)")
        self.query_basic(True)
        self.query_counts(True)
        self.adql_service(True)
        self.adql_keyword(True)
        self.adql_waveband(True)
        self.adql_source(True)
        self.adql_publisher(True)
        self.adql_orderby(True)

    ##
    ##  Tests that make an http request:
    ##
    def query_basic(self, reinit=False):
        result, raw = Registry.query(source='heasarc', service_type='image', return_raw=True)
        if reinit:
            #table2json(result, data_path(self.DATA_FILES['query_basic_result']))
            table2ecsv(result, data_path(self.DATA_FILES['query_basic_result']))
            raw2json(raw, data_path(self.DATA_FILES['query_basic_response']))
        else:
            assert(table_comp(result, data_path(self.DATA_FILES['query_basic_result'])))

    def query_counts(self, reinit=False):
        result, raw = Registry.query_counts('publisher', 15, verbose=True, return_raw=True)
        if reinit:
            #table2json(result, data_path(self.DATA_FILES['query_counts_result']))
            table2ecsv(result, data_path(self.DATA_FILES['query_counts_result']))
            raw2json(raw, data_path(self.DATA_FILES['query_counts_response']))
        else:
            assert(table_comp(result, data_path(self.DATA_FILES['query_counts_result'])))

    def query_timeout(self):
        from requests.exceptions import (Timeout, ReadTimeout)
        myReg = Registry()
        myReg._TIMEOUT = 0.1
        try:
            result = myReg.query(source='heasarc', service_type='image')
        except (Timeout, ReadTimeout, ConnectionError):
            pass
        except Exception as e:
            pytest.fail("Did not get the expected timeout exception but {}".format(e))
        else:
            pytest.fail("Did not get the expected timeout exception but none")

    ##
    ##  None of these actually query a server. Just testing the adql construction.
    ##

    def adql_service(self, reinit=False):
        result = Registry._build_adql(service_type="image")
        if reinit:
            with open(data_path(self.DATA_FILES['adql_service'], reinit), 'w') as f:
                json.dump(result, f)
        else:
            with open(data_path(self.DATA_FILES['adql_service']), 'r') as f:
                reference = json.load(f)
            assert(result == reference)

    def adql_keyword(self, reinit=False):
        result = Registry._build_adql(keyword="foobar", service_type="image")
        if reinit:
            with open(data_path(self.DATA_FILES['adql_keyword'], reinit), 'w') as f:
                json.dump(result, f)
        else:
            with open(data_path(self.DATA_FILES['adql_keyword']), 'r') as f:
                reference = json.load(f)
            assert(result == reference)

    def adql_waveband(self, reinit=False):
        result = Registry._build_adql(waveband='foobar', service_type="image")
        if reinit:
            with open(data_path(self.DATA_FILES['adql_waveband'], reinit), 'w') as f:
                json.dump(result, f)
        else:
            with open(data_path(self.DATA_FILES['adql_waveband']), 'r') as f:
                reference = json.load(f)
            assert(result == reference)

    def adql_source(self, reinit=False):
        result = Registry._build_adql(source='foobar', service_type="image")
        if reinit:
            with open(data_path(self.DATA_FILES['adql_source'], reinit), 'w') as f:
                json.dump(result, f)
        else:
            with open(data_path(self.DATA_FILES['adql_source']), 'r') as f:
                reference = json.load(f)
            assert(result == reference)

    def adql_publisher(self, reinit=False):
        result = Registry._build_adql(publisher='foobar', service_type="image")
        if reinit:
            with open(data_path(self.DATA_FILES['adql_publisher'], reinit), 'w') as f:
                json.dump(result, f)
        else:
            with open(data_path(self.DATA_FILES['adql_publisher']), 'r') as f:
                reference = json.load(f)
            assert(result == reference)

    def adql_orderby(self, reinit=False):
        result = Registry._build_adql(order_by="foobar", service_type="image")
        if reinit:
            with open(data_path(self.DATA_FILES['adql_orderby'], reinit), 'w') as f:
                json.dump(result, f)
        else:
            with open(data_path(self.DATA_FILES['adql_orderby']), 'r') as f:
                reference = json.load(f)
            assert(result == reference)


## This main can regenerate the stored JSON for you after you've run a
## test and checked that the new results are correct.
if __name__ == "__main__":
    tests = TestReg()
    tests.rewrite()
    print(tests.query_basic())
