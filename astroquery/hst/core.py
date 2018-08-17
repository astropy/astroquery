# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""

@author: Javier Duran
@contact: javier.duran@sciops.esa.int

European Space Astronomy Centre (ESAC)
European Space Agency (ESA)

Created on 13 Ago. 2018


"""

#from astroquery.utils import commons
#from astropy import units
#from astropy.units import Quantity
import urllib.request
from . import conf

__all__ = ['Hst', 'HstClass']


class HstClass(object):

    data_url = conf.DATA_ACTION#"http://archives.esac.esa.int/ehst-sl-server/servlet/data-action?"
    metadata_url = conf.METADATA_ACTION#"http://archives.esac.esa.int/ehst-sl-server/servlet/metadata-action?"

    def __init__(self):
        return

    def get_product(self, observation_id, calibration_level="RAW", filename=None, verbose=False):
        obs_id = "OBSERVATION_ID=" + observation_id
        cal_level = "CALIBRATION_LEVEL=" + calibration_level
        link = self.data_url + obs_id + "&" + cal_level
        if filename is None:
            filename = observation_id + ".tar"
        print(link)
        return self.get_file(link, filename, verbose)

    def get_artifact(self, artifact_id, filename=None, verbose=False):
        art_id = "ARTIFACT_ID=" + artifact_id
        link = self.data_url + art_id
        if filename is None:
            filename = artifact_id
        print(link)
        return self.get_file(link, filename, verbose)

    def get_postcard(self, observation_id, calibration_level="RAW", resolution=256, filename=None, verbose=False):
        retri_type = "RETRIEVAL_TYPE=POSTCARD"
        obs_id = "OBSERVATION_ID=" + observation_id
        cal_level = "CALIBRATION_LEVEL=" + calibration_level
        res = "RESOLUTION=" + str(resolution)
        link = self.data_url + retri_type + "&" + obs_id + "&" + cal_level + "&" + res
        if filename is None:
            filename = observation_id + ".tar"
        print(link)
        return self.get_file(link, filename, verbose)

    def get_metadata(self, params, filename=None, verbose=False):
        link = self.metadata_url + params
        if filename is None:
            filename = "metadata.xml"
        print(link)
        return self.get_file(link, filename, verbose)

    def get_file(self, url, filename, verbose=False):
        urllib.request.urlretrieve(url, filename)
        return

Hst = HstClass()
