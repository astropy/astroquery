Astroquery Services by Type
===========================

An index of the services by the type of data they serve.  Some services
perform many tasks and are listed more than once.

Catalogs
--------

The first serve catalogs, which generally return one row of information for
each source (though they may return many catalogs that *each* have one row
for each source)

.. toctree::
  :maxdepth: 1

  alfalfa/alfalfa.rst
  exoplanet_orbit_database/exoplanet_orbit_database.rst
  gama/gama.rst
  ipac/irsa/irsa_dust/irsa_dust.rst
  ipac/irsa/ibe/ibe.rst
  ipac/irsa/irsa.rst
  mast/mast.rst
  ipac/nexsci/nasa_exoplanet_archive.rst
  ipac/ned/ned.rst
  ogle/ogle.rst
  open_exoplanet_catalogue/open_exoplanet_catalogue.rst
  sdss/sdss.rst
  simbad/simbad.rst
  ukidss/ukidss.rst
  vizier/vizier.rst
  vo_conesearch/vo_conesearch.rst
  vsa/vsa.rst
  xmatch/xmatch.rst

Archives
--------

Archive services provide data, usually in FITS images or spectra.  They will
generally return a table listing the available data first.

.. toctree::
  :maxdepth: 1

  alfalfa/alfalfa.rst
  alma/alma.rst
  cadc/cadc.rst
  casda/casda.rst
  esa/hubble/hubble.rst
  esa/jwst/jwst.rst
  esa/xmm_newton/xmm_newton.rst
  eso/eso.rst
  fermi/fermi.rst
  gaia/gaia.rst
  gemini/gemini.rst
  heasarc/heasarc.rst
  ipac/irsa/ibe/ibe.rst
  ipac/irsa/irsa.rst
  magpis/magpis.rst
  mast/mast.rst
  ipac/ned/ned.rst
  nvas/nvas.rst
  sdss/sdss.rst
  skyview/skyview.rst
  ukidss/ukidss.rst
  vsa/vsa.rst

Simulations
-----------

These services query databases of simulated or synthetic data.

.. toctree::
  :maxdepth: 1

  besancon/besancon.rst
  cosmosim/cosmosim.rst

Line List Services
------------------

Services that provide atomic or molecular line lists, as
well as  cross section and collision rates. 

.. toctree::
  :maxdepth: 1

  atomic/atomic.rst
  linelists/cdms/cdms.rst
  hitran/hitran.rst
  jplspec/jplspec.rst
  lamda/lamda.rst
  nist/nist.rst
  splatalogue/splatalogue.rst
  vamdc/vamdc.rst

Other
-----

Other astronomically significant services, that don't fit the
above categories. 

.. toctree::
  :maxdepth: 1

  astrometry_net/astrometry_net.rst
  imcce/imcce.rst
  jplhorizons/jplhorizons.rst
  jplsbdb/jplsbdb.rst
  nasa_ads/nasa_ads.rst
  solarsystem/neodys/neodys.rst
  utils/tap.rst

Topical Collections
-------------------

Some services focusing on similar topics are also collected in
topical submodules.

.. toctree::
  :maxdepth: 1

  image_cutouts/image_cutouts.rst
  solarsystem/solarsystem.rst
