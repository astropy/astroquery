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

    VALID_LE3_PRODUCT_TYPES_CATEGORIES_GROUPS = {
        'Clusters of Galaxies': {
            'GrpCatalog': ['DpdLE3clAMICOModel', 'DpdLE3clDetMergeParams', 'DpdLE3clDetOnMockParams',
                           'DpdLE3clDetInputParams', 'DpdLE3clAmicoAux', 'DpdLE3clAssociations', 'DpdLE3clPzwavAux',
                           'DpdLE3clPZWAVDensity', 'DpdLE3clDetClusters', 'DpdLE3FullDet', 'DpdLE3clCatMergeParams',
                           'DpdLE3clCATParams', 'DpdLE3clCcpInputParams', 'DpdLE3clRichMembers', 'DpdLE3clZClParams',
                           'DpdLE3clGlueMatchParams', 'DpdLE3clMockGlueMatchParams'],
            'GrpClustering': ['DDpdLE3clPkDOA', 'DpdLE3clCovmatTwoPointCov2', 'DpdLE3clPkYam',
                              'DpdLE3clTwoPointAutoCorrPol', 'DpolDpdLE3clCovmatPKCov1'],
            'GrpCOMB': ['DpdLE3clCombConfigurationSet', 'DpdLE3clCombCovMatDeltaSigmaCosmoDep',
                        'DpdLE3clCombCovMatReducedShearCosmoDep', 'DpdLE3clCombCovMatReducedShearCosmoIndep',
                        'DpdLE3clCombRedSheProf', 'DpdLE3clCombStackingCosmoDep', 'DpdLE3clCombStackingCosmoInd',
                        'DpdLE3clCombUCovRedSheProf', 'DpdLE3clCombWLME'],
            'GrpLMF': ['DpdLE3clLMFOutput', 'DpdLE3clLMFParams'],
            'GrpSEL': ['DpdLE3clMatchForSelParams', 'DpdLE3clMockClusters', 'DpdLE3clRedshiftDistrib',
                       'DpdLE3clSelRandom', 'DpdLE3clSelRandomParams', 'DpdLE3clSelSelFunc',
                       'DpdLE3clSelSelFuncInputParams', 'DpdLE3clSelSinfoniaIniClMockInputParams',
                       'DpdLE3clSelSinfoniaMockInputParams', 'DpdLE3clSelSubSample', 'DpdLE3clSinfoniaEllipticity'],
            'GrpTiling': ['DpdLE3clCLTile', 'DpdLE3clCommon', 'DpdLE3clConfigurationSet']},
        'External Data Products': {
            'LE3-ED configuration catalog': ['DpdLE3edConfigurationFile'],
            'LE3-ED match catalog': ['DpdLE3edMatchedCatalog']},
        'Galaxy Clustering Products': {
            '2PCF_PK': ['DpdLE3gcPkCross', 'DpdLE3gcPkDOA', 'DpdLE3gcPkYam', 'DpdLE3gcTwoPointAutoCorr',
                        'DpdLE3gcTwoPointAutoCorrCart', 'DpdLE3gcTwoPointAutoCorrPol', 'DpdLE3gcTwoPointCrossCorr',
                        'DpdLE3gcTwoPointCrossCorrCart', 'DpdLE3gcTwoPointCrossCorrPol', 'DpdLE3gcTwoPointRecAutoCorr',
                        'DpdLE3gcTwoPointRecAutoCorrCart', 'DpdLE3gcTwoPointRecAutoCorrPol',
                        'DpdLE3gcTwoPointRecCrossCorr', 'DpdLE3gcTwoPointRecCrossCorrCart',
                        'DpdLE3gcTwoPointRecCrossCorrPol'],
            '3PCF_BK': ['DpdLE3gcBkMonopole', 'DpdLE3gcBkMultipole', 'DpdLE3gcThreePointAll', 'DpdLE3gcThreePointSin'],
            'CM-2PCF': ['DpdLE3gcCovmatTwoPointCov1D', 'DpdLE3gcCovmatTwoPointCov2Dcart',
                        'DpdLE3gcCovmatTwoPointCov2Dpol', 'DpdLE3gcCovmatTwoPointCovMu',
                        'DpdLE3gcCovmatTwoPointCovPro'],
            'CM-PK': ['DpdLE3gcCovmatPKCov1D', 'DpdLE3gcCovmatPKCov2Dcart', 'DpdLE3gcCovmatPKCov2Dpol']},
        'Internal Data Products': {
            'SEL Config/Stats': ['DpdLE3IDSELConfigurationSet', 'DpdLE3IDSELIDStatistics'],
            'SEL Wide Main': ['DpdLE3IDSELIDCatalog'],
            'SEL Wide': ['DpdLE3IDSELIDSubsampledCatalog'],
            'VMSP Group': ['DpdLE3IDVMSPConfiguration', 'DpdLE3IDVMSPDetectionModel', 'DpdLE3IDVMSPDistModel',
                           'DpdLE3IDVMSPRandomCatalog']},
        'Weak Lensing Products': {
            '2D-MASS': ['DpdTwoDMassConvergenceClusters', 'DpdTwoDMassConvergencePatch',
                        'DpdTwoDMassConvergencePatchesToSphere', 'DpdTwoDMassConvergenceSphere',
                        'DpdTwoDMassParamsConvergenceClusters', 'DpdTwoDMassParamsConvergencePatch',
                        'DpdTwoDMassParamsConvergencePatchesToSphere', 'DpdTwoDMassParamsConvergenceSphere',
                        'DpdTwoDMassParamsPeakCatalogConvergence', 'DpdTwoDMassParamsPeakCatalogMassAperture',
                        'DpdTwoDMassPeakCatalog'],
            '2PCF': ['DpdTwoPCFWLCOSEBIFilter', 'DpdTwoPCFWLParamsCOSEBIShearShear2D', 'DpdTwoPCFWLParamsClPosPos2D',
                     'DpdTwoPCFWLParamsPEBPosShear2D', 'DpdTwoPCFWLParamsPEBShearShear2D', 'DpdTwoPCFWLParamsPosPos2D',
                     'DpdTwoPCFWLParamsPosShear2D', 'DpdTwoPCFWLParamsShearShear2D', 'DpdTwoPCFWLCOSEBIShearShear2D',
                     'DpdTwoPCFWLClPosPos2D', 'DpdTwoPCFWLPEBPosShear2D', 'DpdTwoPCFWLPEBShearShear2D',
                     'DpdTwoPCFWLPosPos2D', 'DpdTwoPCFWLPosShear2D', 'DpdTwoPCFWLShearShear2D',
                     'DpdCovarTwoPCFWLParams', 'DpdCovarTwoPCFWLClPosPos2D', 'DpdCovarTwoPCFWLCOSEBIShearShear2D',
                     'DpdCovarTwoPCFWLPEBPosShear2D', 'DpdCovarTwoPCFWLPEBShearShear2D',
                     'DpdCovarTwoPCFWLPosPos2D', 'DpdCovarTwoPCFWLPosShear2D', 'DpdCovarTwoPCFWLShearShear2D',
                     'DpdCovarTwoPCFWLResampleCOSEBIShearShear2D', 'DpdCovarTwoPCFWLResampleClPosPos2D',
                     'DpdCovarTwoPCFWLResamplePEBPosShear2D', 'DpdCovarTwoPCFWLResamplePEBShearShear2D',
                     'DpdCovarTwoPCFWLResamplePosPos2D', 'DpdCovarTwoPCFWLResamplePosShear2D',
                     'DpdCovarTwoPCFWLResampleShearShear2D'],
            'PK': ['DpdPKWLAlms', 'DpdPKWLCovMatrix2D', 'DpdPKWLEstimate2D', 'DpdPKWLMaps', 'DpdPKWLMixingMatrix2D']},
        'PHZ': {
            'PHZ': ['DpdBinMeanRedshift', 'DpdReferenceSample', 'DpdTomographicBins']}
    }

    PRODUCT_TYPES = ['observation', 'mosaic']

    SCHEMAS = ['sedm']

    VALID_DATALINK_RETRIEVAL_TYPES = ['SPECTRA_BGS', 'SPECTRA_RGS']


conf = Conf()

from .core import Euclid, EuclidClass

__all__ = ['Euclid', 'EuclidClass', 'Conf', 'conf']
