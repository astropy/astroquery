import pickle,json, os
## Why can't I import astroquery.vo ? 
from astroquery.vo import Registry

##
##  Regenerate the output JSON files using:
##  
##  astroquery/vo > python tests/thetests.py 

DATA_FILES = {'query_basic': 'registry_query_basic.json', 
              'adql_service': 'registry_adql_service.json', 
              "adql_keyword":"registry_adql_keyword.json", 
              "adql_waveband":"registry_adql_waveband.json", 
              "adql_source":"registry_adql_source.json", 
              "adql_publisher":"registry_adql_publisher.json", 
              "adql_orderby":"registry_adql_orderby.json", 
              "query_counts":"registry_query_counts.json"
}


## Keep the tests in one place. Import and decorate or init differently in
## test_registry.py or test_registry_remote.py or this main
class TestReg(object):

    def data_path(self,filename,reinit=False):
        """ In case these paths change depending on test methods"""
        data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'data'))
        return os.path.join(data_dir, filename)
    #   if reinit:
    #        data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'data'))
    #    else:
    #        data_dir = os.path.abspath('data')
    #    return os.path.join(data_dir, filename)

    def rewrite(self):
        """Called by main below to re-generate the reference pickle files."""
        print("DEBUGGING: calling test_basic(True)")
        self.test_query_basic(True)
        self.test_query_counts(True)
        self.test_adql_service(True)
        self.test_adql_keyword(True)
        self.test_adql_waveband(True)
        self.test_adql_source(True)
        self.test_adql_publisher(True)
        self.test_adql_orderby(True)


    def table_comp(self,current,filecomp):
        """Compare the resulting Tables"""
        reference=pickle.load(open(filecomp,'rb'))
        ok=True
        ## Check the meta data:
        metadiff={ k : current.meta[k] for k in set(current.meta) - set(reference.meta) }
        if len(metadiff.keys()) > 0: ok=False
        return ok
                              
    ##
    ##  Tests that make an http request:
    ## 
    def test_query_basic(self,reinit=False):
        result = Registry.query(source='heasarc',
                                                service_type='image')
        if reinit:
            pickle.dump(result, open(self.data_path(DATA_FILES['query_basic'],reinit),'wb'))
        else:
            assert(self.table_comp(result,self.data_path(DATA_FILES['query_basic'])))

    def test_query_counts(self,reinit=False):
        result = Registry.query_counts('publisher', 15, verbose=True)
        if reinit:
            pickle.dump(result,open(self.data_path(DATA_FILES['query_counts'],reinit),'wb') )
        else:
            assert(self.table_comp(result,self.data_path(DATA_FILES['query_counts'])))

    def test_query_timeout(self):
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

    def test_adql_service(self,reinit=False):
        result = Registry._build_adql(service_type="image")
        if reinit:
            with open(self.data_path(DATA_FILES['adql_service'],reinit),'w') as f:
                json.dump(result,f)
        else:
            with open(self.data_path(DATA_FILES['adql_service']),'r') as f:
                reference=json.load(f)
            assert(result == reference)

    def test_adql_keyword(self,reinit=False):
        result = Registry._build_adql(keyword="foobar", service_type="image")
        if reinit:
            with open(self.data_path(DATA_FILES['adql_keyword'],reinit),'w') as f:
                json.dump(result,f)
        else:
            with open(self.data_path(DATA_FILES['adql_keyword']),'r') as f:
                reference=json.load(f)
            assert(result == reference)

    def test_adql_waveband(self,reinit=False):
        result = Registry._build_adql(waveband='foobar', service_type="image")
        if reinit:
            with open(self.data_path(DATA_FILES['adql_waveband'],reinit),'w') as f:
                json.dump(result,f)
        else:
            with open(self.data_path(DATA_FILES['adql_waveband']),'r') as f:
                reference=json.load(f)
            assert(result == reference)

    def test_adql_source(self,reinit=False):
        result = Registry._build_adql(source='foobar', service_type="image")
        if reinit:
            with open(self.data_path(DATA_FILES['adql_source'],reinit),'w') as f:
                json.dump(result,f)
        else:
            with open(self.data_path(DATA_FILES['adql_source']),'r') as f:
                reference=json.load(f)
            assert(result == reference)

    def test_adql_publisher(self,reinit=False):
        result = Registry._build_adql(publisher='foobar', service_type="image")
        if reinit:
            with open(self.data_path(DATA_FILES['adql_publisher'],reinit),'w') as f:
                json.dump(result,f)
        else:
            with open(self.data_path(DATA_FILES['adql_publisher']),'r') as f:
                reference=json.load(f)
            assert(result == reference)

    def test_adql_orderby(self,reinit=False):
        result = Registry._build_adql(order_by="foobar", service_type="image")
        if reinit:
            with open(self.data_path(DATA_FILES['adql_orderby'],reinit),'w') as f:
                json.dump(result,f)
        else:
            with open(self.data_path(DATA_FILES['adql_orderby']),'r') as f:
                reference=json.load(f)
            assert(result == reference)




## This main can regenerate the stored JSON for you after you've run a
## test and checked that the new results are correct.
if __name__ == "__main__":
    tests=TestReg()
    tests.rewrite()
