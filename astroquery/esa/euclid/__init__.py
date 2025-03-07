# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
===============
Euclid TAP plus
===============
European Space Astronomy Centre (ESAC)
European Space Agency (ESA)
"""

from astropy import config as _config


class Conf(_config.ConfigNamespace):
    """
    Configuration parameters for `astroquery.esa.euclid`.
    """

    URL_BASE = _config.ConfigItem('https://eas.esac.esa.int/', 'Euclid base URL')

    EUCLID_TAP_SERVER = _config.ConfigItem('https://easidr.esac.esa.int/tap-server/tap', 'Euclid TAP Server')
    EUCLID_DATALINK_SERVER = _config.ConfigItem("https://easidr.esac.esa.int/sas-dd/data?", "Euclid DataLink Server")
    EUCLID_CUTOUT_SERVER = _config.ConfigItem("https://easidr.esac.esa.int/sas-cutout/cutout?", "Euclid Cutout Server")

    ROW_LIMIT = _config.ConfigItem(50,
                                   "Number of rows to return from database query (set to -1 for unlimited).")

    USE_NAMES_OVER_IDS = _config.ConfigItem(True,
                                            "When converting from an astropy.io.votable.tree.TableElement object to "
                                            "an astropy.table.Table object, you can specify whether to give "
                                            "preference to name or ID attributes when naming the columns. By default, "
                                            "ID is given preference. To give name preference, set the value to True:")

    ENVIRONMENTS = {'IDR': {'url_server': 'https://easidr.esac.esa.int/', 'main_table': 'catalogue.mer_catalogue',
                            'main_table_ra_column': 'right_ascension', 'main_table_dec_column': 'declination'},
                    'OTF': {'url_server': 'https://easotf.esac.esa.int/', 'main_table': 'catalogue.mer_catalogue',
                            'main_table_ra_column': 'right_ascension', 'main_table_dec_column': 'declination'},
                    'REG': {'url_server': 'https://easreg.esac.esa.int/',
                            'main_table': 'catalogue.mer_final_catalog_fits_file_regreproc1_r2',
                            'main_table_ra_column': 'right_ascension', 'main_table_dec_column': 'declination'},
                    'PDR': {'url_server': 'https://eas.esac.esa.int/', 'main_table': 'catalogue.mer_catalogue',
                            'main_table_ra_column': 'right_ascension', 'main_table_dec_column': 'declination'}
                    }

    OBSERVATION_STACK_PRODUCTS = ['DpdNirStackedFrame', 'DpdVisStackedFrame']

    MOSAIC_PRODUCTS = ['DpdMerBksMosaic']

    BASIC_DOWNLOAD_DATA_PRODUCTS = ['dpdPhzPfOutputForL3', 'dpdPhzPfOutputCatalog', 'dpdMerFinalCatalog',
                                    'dpdSpePfOutputCatalog', 'dpdSheLensMcChains', 'dpdHealpixBitMaskVMPZ',
                                    'dpdHealpixFootprintMaskVMPZ', 'dpdHealpixCoverageVMPZ', 'dpdHealpixDepthMapVMPZ',
                                    'dpdHealpixInfoMapVMPZ', 'dpdSheBiasParams', 'dpdSheLensMcFinalCatalog',
                                    'dpdSheLensMcRawCatalog', 'dpdSheMetaCalFinalCatalog', 'dpdSheMetaCalRawCatalog',
                                    'dpdSleDetectionOutput', 'dpdSleModelOutput']

    MER_SEGMENTATION_MAP_PRODUCTS = ['DpdMerSegmentationMap']

    RAW_FRAME_PRODUCTS = ['dpdVisRawFrame', 'dpdNispRawFrame']

    CALIBRATED_FRAME_PRODUCTS = ['DpdVisCalibratedQuadFrame', 'DpdNirCalibratedFrame']

    FRAME_CATALOG_PRODUCTS = ['DpdNirStackedFrameCatalog', 'DpdVisStackedFrameCatalog', 'DpdNirCalibratedFrameCatalog',
                              'DpdVisCalibratedFrameCatalog']

    COMBINED_SPECTRA_PRODUCTS = ['DpdSirCombinedSpectra']

    SIR_SCIENCE_FRAME_PRODUCTS = ['dpdSirScienceFrame']

    PRODUCT_TYPES = ['observation', 'mosaic']

    SCHEMAS = ['sedm']

    VALID_DATALINK_RETRIEVAL_TYPES = ['SPECTRA_BGS', 'SPECTRA_RGS']


conf = Conf()

from .core import Euclid, EuclidClass

__all__ = ['Euclid', 'EuclidClass', 'Conf', 'conf']
