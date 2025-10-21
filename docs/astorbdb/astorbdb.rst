.. _astroquery.astorbdb:

*******************************************************************************
Lowell AstorbDB Queries (`astroquery.astorbdb`/astroquery.solarsystem.astorbdb)
*******************************************************************************

Overview
========


The :class:`~astroquery.astorbdb.AstInfoClass` class provides
an interface to the `Asteroid Information
<https://asteroid.lowell.edu/astinfo/>`_ (AstInfo) tool provided as part of
the `Lowell Minor Planet Services <https://https://asteroid.lowell.edu/>`_
which utilize the astorbDB database maintained by
`Lowell Observatory <https://lowell.edu/>`_.

AstInfo provides detailed information on a specific known small body,
including lists of alternate designations, orbit information, and available
published physical and dynamical properties.

This module enables the query of these information for an individual
object into a formatted dictionary or `~collections.OrderedDict` structure
using `~astropy.units` objects where possible.  This module
uses REST interfaces (currently undocumented) used to retrieve data
displayed on the Lowell `Asteroid Information <https://asteroid.lowell.edu/astinfo/>`_
page.

Because of its relevance to Solar System science, this service can
also be accessed from the topical submodule
`astroquery.solarsystem.astorbdb`. The functionality of that service is
identical to the one presented here.

Examples
========

There are several different categories of information that can be obtained
using an AstInfo query:

Albedo data
-----------

This query returns a list of dictionaries of albedo-related data and associated
metadata for a specified object from different published sources.

.. doctest-remote-data::

   >>> from astroquery.astorbdb import AstInfo
   >>> albedos = AstInfo.albedos('656')
   >>> print(albedos)   # doctest: +IGNORE_OUTPUT
   [{'albedo': 0.065, 'albedo_error_lower': -0.002, 'albedo_error_upper': 0.002, 'citation_bibcode': '2011PASJ...63.1117U', 'citation_url': 'https://darts.isas.jaxa.jp/astro/akari/catalogue/AcuA.html', 'count_bands_detection': 2, 'diameter': <Quantity 54.32 km>, 'diameter_error_lower': <Quantity -0.77 km>, 'diameter_error_upper': <Quantity 0.77 km>, 'eta': 0.82, 'eta_error_lower': None, 'eta_error_upper': None, 'measurement_techniques': ['Mid IR photometry'], 'observations_total': 11, 'survey_name': 'Usui et al. (2011)'}, {'albedo': 0.0625, 'albedo_error_lower': -0.015, 'albedo_error_upper': 0.015, 'citation_bibcode': '2004PDSS...12.....T', 'citation_url': 'http://sbn.psi.edu/pds/asteroid/IRAS_A_FPA_3_RDR_IMPS_V6_0.zip', 'count_bands_detection': 3, 'diameter': <Quantity 53.17 km>, 'diameter_error_lower': <Quantity -5.5 km>, 'diameter_error_upper': <Quantity 5.5 km>, 'eta': 0.756, 'eta_error_lower': -1, 'eta_error_upper': 1, 'measurement_techniques': ['Mid IR photometry'], 'observations_total': 18, 'survey_name': 'Infrared Astronomical Satellite (IRAS)'}, {'albedo': 0.075, 'albedo_error_lower': -0.011, 'albedo_error_upper': 0.011, 'citation_bibcode': '2019PDSS..251.....M', 'citation_url': 'http://sbnarchive.psi.edu/pds4/non_mission/neowise_diameters_albedos_V2_0.zip', 'count_bands_detection': 4, 'diameter': <Quantity 48.471 km>, 'diameter_error_lower': <Quantity -0.535 km>, 'diameter_error_upper': <Quantity 0.535 km>, 'eta': 1.033, 'eta_error_lower': -0.021, 'eta_error_upper': 0.021, 'measurement_techniques': ['Mid IR photometry'], 'observations_total': 58, 'survey_name': 'NEOWISE'}, {'albedo': 0.045, 'albedo_error_lower': -0.005, 'albedo_error_upper': 0.005, 'citation_bibcode': '2019PDSS..251.....M', 'citation_url': 'http://sbnarchive.psi.edu/pds4/non_mission/neowise_diameters_albedos_V2_0.zip', 'count_bands_detection': 4, 'diameter': <Quantity 62.604 km>, 'diameter_error_lower': <Quantity -0.512 km>, 'diameter_error_upper': <Quantity 0.512 km>, 'eta': 1.458, 'eta_error_lower': -0.025, 'eta_error_upper': 0.025, 'measurement_techniques': ['Mid IR photometry'], 'observations_total': 46, 'survey_name': 'NEOWISE'}, {'albedo': 0.092, 'albedo_error_lower': -0.041, 'albedo_error_upper': 0.041, 'citation_bibcode': '2019PDSS..251.....M', 'citation_url': 'http://sbnarchive.psi.edu/pds4/non_mission/neowise_diameters_albedos_V2_0.zip', 'count_bands_detection': 2, 'diameter': <Quantity 38.214 km>, 'diameter_error_lower': <Quantity -10.329 km>, 'diameter_error_upper': <Quantity 10.329 km>, 'eta': 0.95, 'eta_error_lower': -0.2, 'eta_error_upper': 0.2, 'measurement_techniques': ['Mid IR photometry'], 'observations_total': 16, 'survey_name': 'NEOWISE'}, {'albedo': 0.069, 'albedo_error_lower': -0.034, 'albedo_error_upper': 0.034, 'citation_bibcode': '2019PDSS..251.....M', 'citation_url': 'http://sbnarchive.psi.edu/pds4/non_mission/neowise_diameters_albedos_V2_0.zip', 'count_bands_detection': 2, 'diameter': <Quantity 45.005 km>, 'diameter_error_lower': <Quantity -15.483 km>, 'diameter_error_upper': <Quantity 15.483 km>, 'eta': 0.95, 'eta_error_lower': -0.2, 'eta_error_upper': 0.2, 'measurement_techniques': ['Mid IR photometry'], 'observations_total': 26, 'survey_name': 'NEOWISE'}, {'albedo': 0.083, 'albedo_error_lower': -0.054, 'albedo_error_upper': 0.054, 'citation_bibcode': '2019PDSS..251.....M', 'citation_url': 'http://sbnarchive.psi.edu/pds4/non_mission/neowise_diameters_albedos_V2_0.zip', 'count_bands_detection': 2, 'diameter': <Quantity 40.12 km>, 'diameter_error_lower': <Quantity -14.369 km>, 'diameter_error_upper': <Quantity 14.369 km>, 'eta': 0.95, 'eta_error_lower': -0.2, 'eta_error_upper': 0.2, 'measurement_techniques': ['Mid IR photometry'], 'observations_total': 22, 'survey_name': 'NEOWISE'}]

Color data
----------

This query returns a list of dictionaries of color data and associated
metadata for a specified object from different published sources.

.. doctest-remote-data::

   >>> from astroquery.astorbdb import AstInfo
   >>> colors = AstInfo.colors('656')
   >>> print(colors)   # doctest: +IGNORE_OUTPUT
   [{'citation_bibcode': '2010PDSS..125.....S', 'citation_url': 'http://sbnarchive.psi.edu/pds3/non_mission/EAR_A_I0054_I0055_5_2MASS_V2_0.zip', 'color': 0.431, 'color_error': 0.035, 'jd': <Time object: scale='utc' format='jd' value=2450770.99139>, 'measurement_techniques': ['Near IR photometry'], 'survey_name': '2 Micron All Sky Survey (2MASS)', 'sys_color': 'J-H'}, {'citation_bibcode': '2010PDSS..125.....S', 'citation_url': 'http://sbnarchive.psi.edu/pds3/non_mission/EAR_A_I0054_I0055_5_2MASS_V2_0.zip', 'color': 0.076, 'color_error': 0.041, 'jd': <Time object: scale='utc' format='jd' value=2450770.99139>, 'measurement_techniques': ['Near IR photometry'], 'survey_name': '2 Micron All Sky Survey (2MASS)', 'sys_color': 'H-K'}, {'citation_bibcode': '2010PDSS..125.....S', 'citation_url': 'http://sbnarchive.psi.edu/pds3/non_mission/EAR_A_I0054_I0055_5_2MASS_V2_0.zip', 'color': 0.382, 'color_error': 0.037, 'jd': <Time object: scale='utc' format='jd' value=2450771.00914>, 'measurement_techniques': ['Near IR photometry'], 'survey_name': '2 Micron All Sky Survey (2MASS)', 'sys_color': 'J-H'}, {'citation_bibcode': '2010PDSS..125.....S', 'citation_url': 'http://sbnarchive.psi.edu/pds3/non_mission/EAR_A_I0054_I0055_5_2MASS_V2_0.zip', 'color': 0.112, 'color_error': 0.043, 'jd': <Time object: scale='utc' format='jd' value=2450771.00914>, 'measurement_techniques': ['Near IR photometry'], 'survey_name': '2 Micron All Sky Survey (2MASS)', 'sys_color': 'H-K'}, {'citation_bibcode': '2010PDSS..125.....S', 'citation_url': 'http://sbnarchive.psi.edu/pds3/non_mission/EAR_A_I0054_I0055_5_2MASS_V2_0.zip', 'color': 0.377, 'color_error': 0.037, 'jd': <Time object: scale='utc' format='jd' value=2450776.94234>, 'measurement_techniques': ['Near IR photometry'], 'survey_name': '2 Micron All Sky Survey (2MASS)', 'sys_color': 'J-H'}, {'citation_bibcode': '2010PDSS..125.....S', 'citation_url': 'http://sbnarchive.psi.edu/pds3/non_mission/EAR_A_I0054_I0055_5_2MASS_V2_0.zip', 'color': 0.145, 'color_error': 0.051, 'jd': <Time object: scale='utc' format='jd' value=2450776.94234>, 'measurement_techniques': ['Near IR photometry'], 'survey_name': '2 Micron All Sky Survey (2MASS)', 'sys_color': 'H-K'}, {'citation_bibcode': '2007PDSS...79.....B', 'citation_url': 'http://sbnarchive.psi.edu/pds3/non_mission/EAR_A_I0287_3_ASTDENIS_V1_0.zip', 'color': 0.42, 'color_error': 0.09, 'jd': <Time object: scale='utc' format='jd' value=2451762.67375>, 'measurement_techniques': ['Near IR photometry'], 'survey_name': 'Deep European Near-Infrared Southern Sky Survey (DENIS)', 'sys_color': 'I-J'}, {'citation_bibcode': '2007PDSS...79.....B', 'citation_url': 'http://sbnarchive.psi.edu/pds3/non_mission/EAR_A_I0287_3_ASTDENIS_V1_0.zip', 'color': 0.37, 'color_error': 0.23, 'jd': <Time object: scale='utc' format='jd' value=2451762.67375>, 'measurement_techniques': ['Near IR photometry'], 'survey_name': 'Deep European Near-Infrared Southern Sky Survey (DENIS)', 'sys_color': 'J-K'}, {'citation_bibcode': '2010PDSS..124.....I', 'citation_url': 'http://sbnarchive.psi.edu/pds3/non_mission/EAR_A_I0035_3_SDSSMOC_V3_0.zip', 'color': 1.54, 'color_error': 0.03, 'jd': <Time object: scale='utc' format='jd' value=2452225.662755839>, 'measurement_techniques': ['Visible photometry'], 'survey_name': 'Sloan Digital Sky Survey (SDSS) Moving Object Catalog (MOC)', 'sys_color': 'u-g'}, {'citation_bibcode': '2010PDSS..124.....I', 'citation_url': 'http://sbnarchive.psi.edu/pds3/non_mission/EAR_A_I0035_3_SDSSMOC_V3_0.zip', 'color': 0.38, 'color_error': 0.03, 'jd': <Time object: scale='utc' format='jd' value=2452225.662755839>, 'measurement_techniques': ['Visible photometry'], 'survey_name': 'Sloan Digital Sky Survey (SDSS) Moving Object Catalog (MOC)', 'sys_color': 'g-r'}, {'citation_bibcode': '2010PDSS..124.....I', 'citation_url': 'http://sbnarchive.psi.edu/pds3/non_mission/EAR_A_I0035_3_SDSSMOC_V3_0.zip', 'color': 0.14, 'color_error': 0.03, 'jd': <Time object: scale='utc' format='jd' value=2452225.662755839>, 'measurement_techniques': ['Visible photometry'], 'survey_name': 'Sloan Digital Sky Survey (SDSS) Moving Object Catalog (MOC)', 'sys_color': 'r-i'}, {'citation_bibcode': '2010PDSS..124.....I', 'citation_url': 'http://sbnarchive.psi.edu/pds3/non_mission/EAR_A_I0035_3_SDSSMOC_V3_0.zip', 'color': 0.08, 'color_error': 0.03, 'jd': <Time object: scale='utc' format='jd' value=2452225.662755839>, 'measurement_techniques': ['Visible photometry'], 'survey_name': 'Sloan Digital Sky Survey (SDSS) Moving Object Catalog (MOC)', 'sys_color': 'i-z'}]



Designation information
-----------------------

This query returns a dictionary containing information about a specified object's primary and
alternate designations, and name and number, if those have been assigned.

.. doctest-remote-data::

   >>> from astroquery.astorbdb import AstInfo
   >>> designations = AstInfo.designations('656')
   >>> print(designations)   # doctest: +IGNORE_OUTPUT
   {'alternate_designations': ['1954 HJ', 'A908 BJ'], 'name': 'Beagle', 'number': 656, 'primary_designation': 'A917 ST'}

Dynamical family information
----------------------------

This query returns a list of dictionaries containing information about identified
dynamical family associations for a specified object from different published sources.

.. doctest-remote-data::

   >>> from astroquery.astorbdb import AstInfo
   >>> dynfamily = AstInfo.dynamicalfamily('656')
   >>> print(dynfamily)   # doctest: +IGNORE_OUTPUT
   [{'citation_bibcode': '2015PDSS..234.....N', 'citation_url': 'http://sbn.psi.edu/pds/asteroid/EAR_A_VARGBDET_5_NESVORNYFAM_V3_0.zip', 'family': 'Themis', 'measurement_techniques': ['Simulation'], 'survey_name': 'Nesvorny et al. (2015)'}, {'citation_bibcode': '2015PDSS..234.....N', 'citation_url': 'http://sbn.psi.edu/pds/asteroid/EAR_A_VARGBDET_5_NESVORNYFAM_V3_0.zip', 'family': 'Beagle', 'measurement_techniques': ['Simulation'], 'survey_name': 'Nesvorny et al. (2015)'}]


Orbital elements
----------------

This query returns a dictionary containing orbital elements, dynamical classification, and
absolute magnitude for a specified object.

.. doctest-remote-data::

   >>> from astroquery.astorbdb import AstInfo
   >>> elements = AstInfo.elements('656')
   >>> print(elements)   # doctest: +IGNORE_OUTPUT
   {'a': <Quantity 3.15609077 AU>, 'aphelion_dist': <Quantity 3.56673761 AU>, 'delta_v': None, 'dyn_type_json': ['mba', 'outer_belt'], 'e': 0.13011249522634394, 'ecc_anomaly': <Quantity 332.92103576 deg>, 'epoch': <Time object: scale='utc' format='isot' value=2025-11-21T00:00:00.000>, 'h': <Quantity 10.06 mag>, 'i': <Quantity 336.3146393 deg>, 'long_of_perihelion': <Quantity 153.38815851 deg>, 'm': <Quantity 336.3146393 deg>, 'moid_earth': <Quantity 1.75595519 AU>, 'moid_jupiter': <Quantity 1.42867539 AU>, 'moid_mars': <Quantity 1.08220406 AU>, 'moid_mercury': <Quantity 2.37964567 AU>, 'moid_neptune': <Quantity 26.36882829 AU>, 'moid_saturn': <Quantity 5.92294858 AU>, 'moid_uranus': <Quantity 15.50846879 AU>, 'moid_venus': <Quantity 2.02854037 AU>, 'node': <Quantity 184.15860074 deg>, 'peri': <Quantity 329.22955777 deg>, 'q': <Quantity 2.74544392 AU>, 'r': <Quantity 2.79045903 AU>, 'tisserand_param': 3.1931457522146633, 'true_anomaly': <Quantity 329.30364789 deg>, 'x': <Quantity -1.50717539 AU>, 'y': <Quantity 2.16335715 AU>, 'z': <Quantity 0.91376681 AU>}

Escape route probabilities
--------------------------

This query returns computed probabilities, where available, for a specified near-Earth
object for different escape routes from the main asteroid belt.

.. doctest-remote-data::

   >>> from astroquery.astorbdb import AstInfo
   >>> escaperoutes = AstInfo.escaperoutes('3200')
   >>> print(escaperoutes)   # doctest: +IGNORE_OUTPUT
   [{'citation_bibcode': '2018Icar..312..181G', 'citation_url': 'https://ui.adsabs.harvard.edu/abs/2018Icar..312..181G/abstract', 'dn': 'NaN', 'dp21_complex': 0, 'dp31_complex': 0.02092, 'dp52_complex': 0.01237, 'dp_hungaria': 0.02218, 'dp_jfc': 0, 'dp_nu6_complex': 0.02956, 'dp_phocaea': 0.00804, 'epoch': <Time object: scale='utc' format='isot' value=2021-07-05T00:00:00.000>, 'extrapolated': True, 'interpolated': False, 'measurement_techniques': None, 'n': 'NaN', 'p21_complex': 0, 'p31_complex': 0.09464, 'p52_complex': 0.05353, 'p_hungaria': 0.18482, 'p_jfc': 0, 'p_nu6_complex': 0.64189, 'p_phocaea': 0.02511, 'survey_name': 'debiased absolute-magnitude and orbit distributions of source regions for NEOs'}]

Lightcurve data
---------------

This query returns a list of dictionaries containing lightcurve-related data
for a specified object from different published sources.

.. doctest-remote-data::

   >>> from astroquery.astorbdb import AstInfo
   >>> lightcurves = AstInfo.lightcurves('656')
   >>> print(lightcurves)   # doctest: +IGNORE_OUTPUT
   [{'ambiguous_period': False, 'amp_flag': '', 'amp_max': <Quantity 1.2 mag>, 'amp_min': <Quantity 0.57 mag>, 'citation_bibcode': '2009Icar..202..134W', 'citation_url': 'http://www.minorplanet.info/datazips/LCLIST_PUB_2018JUN.zip', 'measurement_techniques': ['Literature compilation'], 'non_principal_axis_rotator': False, 'notes': '', 'period': <Quantity 7.035 h>, 'period_desc': '', 'period_flag': '', 'quality_code': '3', 'sparse_data': False, 'survey_name': 'Asteroid Lightcurve Database (LCDB)', 'wide_field': False}]

Orbit fitting data
------------------

This query returns a dictionary containing data pertaining to the current orbit fit
of a specified object.

.. doctest-remote-data::

   >>> from astroquery.astorbdb import AstInfo
   >>> orbit = AstInfo.orbit('656')
   >>> print(orbit)   # doctest: +IGNORE_OUTPUT
   {'a1con': <Quantity 0. AU / d2>, 'a2con': <Quantity 0. AU / d2>, 'a3con': <Quantity 0. AU / d2>, 'arc': <Quantity 117.17 yr>, 'autores': 2.3, 'ceu': 0.009522099593679315, 'ceuderiv': 4.212561547732211e-05, 'date10': '2032-02-26T00:00:00', 'dateceu': '2025-09-25T00:00:00', 'dateimp': '2032-02-26T00:00:00', 'datenext': '2026-01-18T00:00:00', 'ephname': 'DE440', 'firstobs': '1908-01-26T00:00:00', 'j_astmass': '[4.74e-10, 1.02e-10, 1.35e-11, 1.31e-10, 5.29e-11, 1.31e-11, 1.1e-11, 1.67e-11, 1.48e-11, 1.82e-11]', 'j_cor': '[[0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [-0.004055185085832673, 0.0, 0.0, 0.0, 0.0, 0.0], [-0.0015645090377908774, -0.0041532120783056925, 0.0, 0.0, 0.0, 0.0], [0.0004584295201142792, -0.0010057748591726862, 0.08978899859165648, 0.0, 0.0, 0.0], [0.0030326801090361935, 0.01035878576323464, -0.08973018649166371, -0.999188105713059, 0.0, 0.0], [0.5410584860536005, -0.16367214117855808, -0.0006228258128981631, 0.0007282603613923922, -0.03201486515235673, 0.0]]', 'j_cov1diag': '[2.9584477261878723e-09, 1.4514969434683615e-08, 1.653314816879276e-06, 0.00014856989283522812, 0.0001487059222312608, 7.0006681942969005e-06]', 'j_eleerr': '[115.82335500749508, 336.6621269260838, 184.51833574323067, 0.5008760510411905, 0.12365750830974455, 3.158409289585422]', 'j_iastuse': '[1, 2, 3, 4, 10, 15, 31, 52, 511, 704, 16, 65, 88, 107, 7, 87]', 'jdeperr': 2439364.6, 'lastobs': '2025-03-28T00:00:00', 'met1': 4.3059e-12, 'met2': 8.8076e-08, 'met3': 4.0612e-08, 'met4': 4.1692e-08, 'met5': 4.1527e-08, 'nappar': 58, 'nsing': 10, 'nuse': 5624, 'orbcomputer': 'L.H. Wasserman ', 'orbdate': '2025-04-12T00:00:00', 'orbqual': 7.06, 'qsky10': 0.019, 'qskyimp': 0.019, 'qskynext': 0.016, 'qualimp': 0, 'ref': 'O914123', 'resmax': 2.29, 'rmso': 0.35, 'tauc': 0, 'timefac': 0.01}

Taxonomy information
--------------------

This query returns a list of dictionaries containing taxonomic classifications, where
available, for a specified object from different published sources.

.. doctest-remote-data::

   >>> from astroquery.astorbdb import AstInfo
   >>> taxonomies = AstInfo.taxonomies('656')
   >>> print(taxonomies)   # doctest: +IGNORE_OUTPUT
   [{'citation_bibcode': '2011PDSS..145.....H', 'citation_url': 'http://sbnarchive.psi.edu/pds4/non_mission/ast.sdss-based-taxonomy.zip', 'measurement_techniques': ['Visible photometry'], 'modifier': '', 'survey_name': 'Carvano et al. (2010)', 'taxonomy': 'C', 'taxonomy_system': 'Carvano_SDSS'}, {'citation_bibcode': '2013Icar..226..723D', 'citation_url': 'http://www.mit.edu/~fdemeo/publications/alluniq_adr4.dat', 'measurement_techniques': ['Visible photometry'], 'modifier': '', 'survey_name': 'DeMeo et al. (2013)', 'taxonomy': 'C', 'taxonomy_system': 'DeMeo_Carry_SDSS'}]

All asteroid data
-----------------

This query returns a compilation in `~collections.OrderedDict` form of the
results of all of queries listed above for the specified object.

.. doctest-remote-data::

   >>> from astroquery.astorbdb import AstInfo
   >>> all_astinfo = AstInfo.all_astinfo('656')
   >>> print(all_astinfo)   # doctest: +IGNORE_OUTPUT
   OrderedDict({'designations': {'alternate_designations': ['1954 HJ', 'A908 BJ'], 'name': 'Beagle', 'number': 656, 'primary_designation': 'A917 ST'}, 'elements': {'a': <Quantity 3.15609077 AU>, 'aphelion_dist': <Quantity 3.56673761 AU>, 'delta_v': None, 'dyn_type_json': ['mba', 'outer_belt'], 'e': 0.13011249522634394, 'ecc_anomaly': <Quantity 332.92103576 deg>, 'epoch': <Time object: scale='utc' format='isot' value=2025-11-21T00:00:00.000>, 'h': <Quantity 10.06 mag>, 'i': <Quantity 336.3146393 deg>, 'long_of_perihelion': <Quantity 153.38815851 deg>, 'm': <Quantity 336.3146393 deg>, 'moid_earth': <Quantity 1.75595519 AU>, 'moid_jupiter': <Quantity 1.42867539 AU>, 'moid_mars': <Quantity 1.08220406 AU>, 'moid_mercury': <Quantity 2.37964567 AU>, 'moid_neptune': <Quantity 26.36882829 AU>, 'moid_saturn': <Quantity 5.92294858 AU>, 'moid_uranus': <Quantity 15.50846879 AU>, 'moid_venus': <Quantity 2.02854037 AU>, 'node': <Quantity 184.15860074 deg>, 'peri': <Quantity 329.22955777 deg>, 'q': <Quantity 2.74544392 AU>, 'r': <Quantity 2.79045903 AU>, 'tisserand_param': 3.1931457522146633, 'true_anomaly': <Quantity 329.30364789 deg>, 'x': <Quantity -1.50717539 AU>, 'y': <Quantity 2.16335715 AU>, 'z': <Quantity 0.91376681 AU>}, 'orbit': {'a1con': <Quantity 0. AU / d2>, 'a2con': <Quantity 0. AU / d2>, 'a3con': <Quantity 0. AU / d2>, 'arc': <Quantity 117.17 yr>, 'autores': 2.3, 'ceu': 0.009522099593679315, 'ceuderiv': 4.212561547732211e-05, 'date10': '2032-02-26T00:00:00', 'dateceu': '2025-09-25T00:00:00', 'dateimp': '2032-02-26T00:00:00', 'datenext': '2026-01-18T00:00:00', 'ephname': 'DE440', 'firstobs': '1908-01-26T00:00:00', 'j_astmass': '[4.74e-10, 1.02e-10, 1.35e-11, 1.31e-10, 5.29e-11, 1.31e-11, 1.1e-11, 1.67e-11, 1.48e-11, 1.82e-11]', 'j_cor': '[[0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [-0.004055185085832673, 0.0, 0.0, 0.0, 0.0, 0.0], [-0.0015645090377908774, -0.0041532120783056925, 0.0, 0.0, 0.0, 0.0], [0.0004584295201142792, -0.0010057748591726862, 0.08978899859165648, 0.0, 0.0, 0.0], [0.0030326801090361935, 0.01035878576323464, -0.08973018649166371, -0.999188105713059, 0.0, 0.0], [0.5410584860536005, -0.16367214117855808, -0.0006228258128981631, 0.0007282603613923922, -0.03201486515235673, 0.0]]', 'j_cov1diag': '[2.9584477261878723e-09, 1.4514969434683615e-08, 1.653314816879276e-06, 0.00014856989283522812, 0.0001487059222312608, 7.0006681942969005e-06]', 'j_eleerr': '[115.82335500749508, 336.6621269260838, 184.51833574323067, 0.5008760510411905, 0.12365750830974455, 3.158409289585422]', 'j_iastuse': '[1, 2, 3, 4, 10, 15, 31, 52, 511, 704, 16, 65, 88, 107, 7, 87]', 'jdeperr': 2439364.6, 'lastobs': '2025-03-28T00:00:00', 'met1': 4.3059e-12, 'met2': 8.8076e-08, 'met3': 4.0612e-08, 'met4': 4.1692e-08, 'met5': 4.1527e-08, 'nappar': 58, 'nsing': 10, 'nuse': 5624, 'orbcomputer': 'L.H. Wasserman ', 'orbdate': '2025-04-12T00:00:00', 'orbqual': 7.06, 'qsky10': 0.019, 'qskyimp': 0.019, 'qskynext': 0.016, 'qualimp': 0, 'ref': 'O914123', 'resmax': 2.29, 'rmso': 0.35, 'tauc': 0, 'timefac': 0.01}, 'albedos': [{'albedo': 0.065, 'albedo_error_lower': -0.002, 'albedo_error_upper': 0.002, 'citation_bibcode': '2011PASJ...63.1117U', 'citation_url': 'https://darts.isas.jaxa.jp/astro/akari/catalogue/AcuA.html', 'count_bands_detection': 2, 'diameter': <Quantity 54.32 km>, 'diameter_error_lower': <Quantity -0.77 km>, 'diameter_error_upper': <Quantity 0.77 km>, 'eta': 0.82, 'eta_error_lower': None, 'eta_error_upper': None, 'measurement_techniques': ['Mid IR photometry'], 'observations_total': 11, 'survey_name': 'Usui et al. (2011)'}, {'albedo': 0.0625, 'albedo_error_lower': -0.015, 'albedo_error_upper': 0.015, 'citation_bibcode': '2004PDSS...12.....T', 'citation_url': 'http://sbn.psi.edu/pds/asteroid/IRAS_A_FPA_3_RDR_IMPS_V6_0.zip', 'count_bands_detection': 3, 'diameter': <Quantity 53.17 km>, 'diameter_error_lower': <Quantity -5.5 km>, 'diameter_error_upper': <Quantity 5.5 km>, 'eta': 0.756, 'eta_error_lower': -1, 'eta_error_upper': 1, 'measurement_techniques': ['Mid IR photometry'], 'observations_total': 18, 'survey_name': 'Infrared Astronomical Satellite (IRAS)'}, {'albedo': 0.075, 'albedo_error_lower': -0.011, 'albedo_error_upper': 0.011, 'citation_bibcode': '2019PDSS..251.....M', 'citation_url': 'http://sbnarchive.psi.edu/pds4/non_mission/neowise_diameters_albedos_V2_0.zip', 'count_bands_detection': 4, 'diameter': <Quantity 48.471 km>, 'diameter_error_lower': <Quantity -0.535 km>, 'diameter_error_upper': <Quantity 0.535 km>, 'eta': 1.033, 'eta_error_lower': -0.021, 'eta_error_upper': 0.021, 'measurement_techniques': ['Mid IR photometry'], 'observations_total': 58, 'survey_name': 'NEOWISE'}, {'albedo': 0.045, 'albedo_error_lower': -0.005, 'albedo_error_upper': 0.005, 'citation_bibcode': '2019PDSS..251.....M', 'citation_url': 'http://sbnarchive.psi.edu/pds4/non_mission/neowise_diameters_albedos_V2_0.zip', 'count_bands_detection': 4, 'diameter': <Quantity 62.604 km>, 'diameter_error_lower': <Quantity -0.512 km>, 'diameter_error_upper': <Quantity 0.512 km>, 'eta': 1.458, 'eta_error_lower': -0.025, 'eta_error_upper': 0.025, 'measurement_techniques': ['Mid IR photometry'], 'observations_total': 46, 'survey_name': 'NEOWISE'}, {'albedo': 0.092, 'albedo_error_lower': -0.041, 'albedo_error_upper': 0.041, 'citation_bibcode': '2019PDSS..251.....M', 'citation_url': 'http://sbnarchive.psi.edu/pds4/non_mission/neowise_diameters_albedos_V2_0.zip', 'count_bands_detection': 2, 'diameter': <Quantity 38.214 km>, 'diameter_error_lower': <Quantity -10.329 km>, 'diameter_error_upper': <Quantity 10.329 km>, 'eta': 0.95, 'eta_error_lower': -0.2, 'eta_error_upper': 0.2, 'measurement_techniques': ['Mid IR photometry'], 'observations_total': 16, 'survey_name': 'NEOWISE'}, {'albedo': 0.069, 'albedo_error_lower': -0.034, 'albedo_error_upper': 0.034, 'citation_bibcode': '2019PDSS..251.....M', 'citation_url': 'http://sbnarchive.psi.edu/pds4/non_mission/neowise_diameters_albedos_V2_0.zip', 'count_bands_detection': 2, 'diameter': <Quantity 45.005 km>, 'diameter_error_lower': <Quantity -15.483 km>, 'diameter_error_upper': <Quantity 15.483 km>, 'eta': 0.95, 'eta_error_lower': -0.2, 'eta_error_upper': 0.2, 'measurement_techniques': ['Mid IR photometry'], 'observations_total': 26, 'survey_name': 'NEOWISE'}, {'albedo': 0.083, 'albedo_error_lower': -0.054, 'albedo_error_upper': 0.054, 'citation_bibcode': '2019PDSS..251.....M', 'citation_url': 'http://sbnarchive.psi.edu/pds4/non_mission/neowise_diameters_albedos_V2_0.zip', 'count_bands_detection': 2, 'diameter': <Quantity 40.12 km>, 'diameter_error_lower': <Quantity -14.369 km>, 'diameter_error_upper': <Quantity 14.369 km>, 'eta': 0.95, 'eta_error_lower': -0.2, 'eta_error_upper': 0.2, 'measurement_techniques': ['Mid IR photometry'], 'observations_total': 22, 'survey_name': 'NEOWISE'}], 'colors': [{'citation_bibcode': '2010PDSS..125.....S', 'citation_url': 'http://sbnarchive.psi.edu/pds3/non_mission/EAR_A_I0054_I0055_5_2MASS_V2_0.zip', 'color': 0.431, 'color_error': 0.035, 'jd': <Time object: scale='utc' format='jd' value=2450770.99139>, 'measurement_techniques': ['Near IR photometry'], 'survey_name': '2 Micron All Sky Survey (2MASS)', 'sys_color': 'J-H'}, {'citation_bibcode': '2010PDSS..125.....S', 'citation_url': 'http://sbnarchive.psi.edu/pds3/non_mission/EAR_A_I0054_I0055_5_2MASS_V2_0.zip', 'color': 0.076, 'color_error': 0.041, 'jd': <Time object: scale='utc' format='jd' value=2450770.99139>, 'measurement_techniques': ['Near IR photometry'], 'survey_name': '2 Micron All Sky Survey (2MASS)', 'sys_color': 'H-K'}, {'citation_bibcode': '2010PDSS..125.....S', 'citation_url': 'http://sbnarchive.psi.edu/pds3/non_mission/EAR_A_I0054_I0055_5_2MASS_V2_0.zip', 'color': 0.382, 'color_error': 0.037, 'jd': <Time object: scale='utc' format='jd' value=2450771.00914>, 'measurement_techniques': ['Near IR photometry'], 'survey_name': '2 Micron All Sky Survey (2MASS)', 'sys_color': 'J-H'}, {'citation_bibcode': '2010PDSS..125.....S', 'citation_url': 'http://sbnarchive.psi.edu/pds3/non_mission/EAR_A_I0054_I0055_5_2MASS_V2_0.zip', 'color': 0.112, 'color_error': 0.043, 'jd': <Time object: scale='utc' format='jd' value=2450771.00914>, 'measurement_techniques': ['Near IR photometry'], 'survey_name': '2 Micron All Sky Survey (2MASS)', 'sys_color': 'H-K'}, {'citation_bibcode': '2010PDSS..125.....S', 'citation_url': 'http://sbnarchive.psi.edu/pds3/non_mission/EAR_A_I0054_I0055_5_2MASS_V2_0.zip', 'color': 0.377, 'color_error': 0.037, 'jd': <Time object: scale='utc' format='jd' value=2450776.94234>, 'measurement_techniques': ['Near IR photometry'], 'survey_name': '2 Micron All Sky Survey (2MASS)', 'sys_color': 'J-H'}, {'citation_bibcode': '2010PDSS..125.....S', 'citation_url': 'http://sbnarchive.psi.edu/pds3/non_mission/EAR_A_I0054_I0055_5_2MASS_V2_0.zip', 'color': 0.145, 'color_error': 0.051, 'jd': <Time object: scale='utc' format='jd' value=2450776.94234>, 'measurement_techniques': ['Near IR photometry'], 'survey_name': '2 Micron All Sky Survey (2MASS)', 'sys_color': 'H-K'}, {'citation_bibcode': '2007PDSS...79.....B', 'citation_url': 'http://sbnarchive.psi.edu/pds3/non_mission/EAR_A_I0287_3_ASTDENIS_V1_0.zip', 'color': 0.42, 'color_error': 0.09, 'jd': <Time object: scale='utc' format='jd' value=2451762.67375>, 'measurement_techniques': ['Near IR photometry'], 'survey_name': 'Deep European Near-Infrared Southern Sky Survey (DENIS)', 'sys_color': 'I-J'}, {'citation_bibcode': '2007PDSS...79.....B', 'citation_url': 'http://sbnarchive.psi.edu/pds3/non_mission/EAR_A_I0287_3_ASTDENIS_V1_0.zip', 'color': 0.37, 'color_error': 0.23, 'jd': <Time object: scale='utc' format='jd' value=2451762.67375>, 'measurement_techniques': ['Near IR photometry'], 'survey_name': 'Deep European Near-Infrared Southern Sky Survey (DENIS)', 'sys_color': 'J-K'}, {'citation_bibcode': '2010PDSS..124.....I', 'citation_url': 'http://sbnarchive.psi.edu/pds3/non_mission/EAR_A_I0035_3_SDSSMOC_V3_0.zip', 'color': 1.54, 'color_error': 0.03, 'jd': <Time object: scale='utc' format='jd' value=2452225.662755839>, 'measurement_techniques': ['Visible photometry'], 'survey_name': 'Sloan Digital Sky Survey (SDSS) Moving Object Catalog (MOC)', 'sys_color': 'u-g'}, {'citation_bibcode': '2010PDSS..124.....I', 'citation_url': 'http://sbnarchive.psi.edu/pds3/non_mission/EAR_A_I0035_3_SDSSMOC_V3_0.zip', 'color': 0.38, 'color_error': 0.03, 'jd': <Time object: scale='utc' format='jd' value=2452225.662755839>, 'measurement_techniques': ['Visible photometry'], 'survey_name': 'Sloan Digital Sky Survey (SDSS) Moving Object Catalog (MOC)', 'sys_color': 'g-r'}, {'citation_bibcode': '2010PDSS..124.....I', 'citation_url': 'http://sbnarchive.psi.edu/pds3/non_mission/EAR_A_I0035_3_SDSSMOC_V3_0.zip', 'color': 0.14, 'color_error': 0.03, 'jd': <Time object: scale='utc' format='jd' value=2452225.662755839>, 'measurement_techniques': ['Visible photometry'], 'survey_name': 'Sloan Digital Sky Survey (SDSS) Moving Object Catalog (MOC)', 'sys_color': 'r-i'}, {'citation_bibcode': '2010PDSS..124.....I', 'citation_url': 'http://sbnarchive.psi.edu/pds3/non_mission/EAR_A_I0035_3_SDSSMOC_V3_0.zip', 'color': 0.08, 'color_error': 0.03, 'jd': <Time object: scale='utc' format='jd' value=2452225.662755839>, 'measurement_techniques': ['Visible photometry'], 'survey_name': 'Sloan Digital Sky Survey (SDSS) Moving Object Catalog (MOC)', 'sys_color': 'i-z'}], 'taxonomies': [{'citation_bibcode': '2011PDSS..145.....H', 'citation_url': 'http://sbnarchive.psi.edu/pds4/non_mission/ast.sdss-based-taxonomy.zip', 'measurement_techniques': ['Visible photometry'], 'modifier': '', 'survey_name': 'Carvano et al. (2010)', 'taxonomy': 'C', 'taxonomy_system': 'Carvano_SDSS'}, {'citation_bibcode': '2013Icar..226..723D', 'citation_url': 'http://www.mit.edu/~fdemeo/publications/alluniq_adr4.dat', 'measurement_techniques': ['Visible photometry'], 'modifier': '', 'survey_name': 'DeMeo et al. (2013)', 'taxonomy': 'C', 'taxonomy_system': 'DeMeo_Carry_SDSS'}], 'lightcurves': [{'ambiguous_period': False, 'amp_flag': '', 'amp_max': <Quantity 1.2 mag>, 'amp_min': <Quantity 0.57 mag>, 'citation_bibcode': '2009Icar..202..134W', 'citation_url': 'http://www.minorplanet.info/datazips/LCLIST_PUB_2018JUN.zip', 'measurement_techniques': ['Literature compilation'], 'non_principal_axis_rotator': False, 'notes': '', 'period': <Quantity 7.035 h>, 'period_desc': '', 'period_flag': '', 'quality_code': '3', 'sparse_data': False, 'survey_name': 'Asteroid Lightcurve Database (LCDB)', 'wide_field': False}], 'dynamicalfamily': [{'citation_bibcode': '2015PDSS..234.....N', 'citation_url': 'http://sbn.psi.edu/pds/asteroid/EAR_A_VARGBDET_5_NESVORNYFAM_V3_0.zip', 'family': 'Themis', 'measurement_techniques': ['Simulation'], 'survey_name': 'Nesvorny et al. (2015)'}, {'citation_bibcode': '2015PDSS..234.....N', 'citation_url': 'http://sbn.psi.edu/pds/asteroid/EAR_A_VARGBDET_5_NESVORNYFAM_V3_0.zip', 'family': 'Beagle', 'measurement_techniques': ['Simulation'], 'survey_name': 'Nesvorny et al. (2015)'}], 'escaperoutes': []})

Output
======

Dictionaries returned by these queries contain a number of items
pertaining to different properties of the object in question.  In
order to use one of these items, you can access it like any dictionary
item:

.. code-block:: python

   >>> elements['a']   # doctest: +REMOTE_DATA
   <Quantity 3.15609077 AU>

Note that many of the items in the output dictionaries are associated
with `~astropy.units` which can be readily used for
transformations. For instance, if you are interested in the minimum
orbit intersection distance of the target with respect to Jupiter
(``moid_jup``) expressed in km instead of au, you can use:

.. code-block:: python

   >>> print(elements['moid_jupiter'].to('km'))    # doctest: +REMOTE_DATA
   213726796.8838375 km



Acknowledgements
================

This submodule makes use of the `Lowell Minor Planet Services
<https://asteroid.lowell.edu/>`_ system.

The development of this submodule is funded through NASA PDART
Grant No. 80NSSC18K0987 to the `sbpy project <https://sbpy.org>`_.


Reference/API
=============

.. automodapi:: astroquery.astorbdb
    :no-inheritance-diagram:
