# Licensed under a 3-clause BSD style license - see LICENSE.rst


from . import conf
from ..wfau import BaseWFAUClass, clean_catalog

__all__ = ['Vsa', 'VsaClass', 'clean_catalog']


class VsaClass(BaseWFAUClass):

    """
    The VsaQuery class.  Must instantiate this class in order to make any
    queries.  Allows registered users to login, but defaults to using the
    public Vsa data sets.
    """
    BASE_URL = conf.server
    LOGIN_URL = BASE_URL + "DBLogin"
    IMAGE_URL = BASE_URL + "GetImage"
    ARCHIVE_URL = BASE_URL + "ImageList"
    REGION_URL = BASE_URL + "WSASQL"
    CROSSID_URL = BASE_URL + "CrossID"
    TIMEOUT = conf.timeout
    IMAGE_FORM = 'VgetImage_form.jsp'
    CROSSID_FORM = 'VcrossID_form.jsp'

    filters = {'all': 'all', 'Z': 1, 'Y': 2, 'J': 3,
               'H': 4, 'Ks': 5, 'NB118': 9, 'NB980': 10}

    frame_types = {'tilestack': 'tilestack', 'stack': 'stack',
                   'normal': 'normal', 'deep_stack': 'deep%stack',
                   'confidence': 'conf', 'difference': 'diff',
                   'all': 'all'}

    programmes_short = {'VHS': 110,
                        'VVV': 120,
                        'VMC': 130,
                        'VIKING': 140,
                        'VIDEO': 150,
                        'UltraVISTA': 160,
                        'Calibration': 200}

    programmes_long = {'VISTA Hemisphere Survey': 110,
                       'VISTA Variables in the Via Lactea': 120,
                       'VISTA Magellanic Clouds Survey': 130,
                       'VISTA Kilo-degree Infrared Galaxy Survey': 140,
                       'VISTA Deep Extragalactic Observations': 150,
                       'An ultra-deep survey with VISTA': 160,
                       'Calibration data': 200}

    all_databases = ('VHSDR4', 'VHSDR3', 'VHSDR2', 'VHSDR1', 'VVVDR4',
                     'VVVDR2', 'VVVDR1', 'VMCDR4', 'VMCDR3', 'VMCDR2',
                     'VMCDR1', 'VIKINGDR4', 'VIKINGDR3', 'VIKINGDR2',
                     'VIDEODR5', 'VIDEODR4', 'VIDEODR3', 'VIDEODR2',
                     'VISTAOPENTIME')

    # apparently needed for some queries
    archive = 'VSA'

    def __init__(self, username=None, password=None, community=None,
                 database='VVVDR4', programme_id='all'):
        super(VsaClass, self).__init__(database=database,
                                       programme_id=programme_id,
                                       username=username,
                                       community=community,
                                       password=password)

        self.BASE_URL = 'http://horus.roe.ac.uk:8080/vdfs/'
        self.LOGIN_URL = self.BASE_URL + "DBLogin"
        self.IMAGE_URL = self.BASE_URL + "GetImage"
        self.ARCHIVE_URL = self.BASE_URL + "ImageList"
        self.REGION_URL = self.BASE_URL + "WSASQL"


Vsa = VsaClass()
