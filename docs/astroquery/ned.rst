.. _astroquery.ned:

******************************
NED Queries (`astroquery.ned`)
******************************

Module containing a series of functions that execute queries to the NASA Extragalactic Database (NED): 

 * :func:`query_ned_by_objname`		- return one of several data tables based on object name 
 * :func:`query_ned_nearname`		- return data on objects within a specified angular 
                    distance to a target
 * :func:`query_ned_near_iauname`	- return data on objects within a specified angular 
                    distance to a target (IAU naming convention)
 * :func:`query_ned_by_refcode`		- return data on objects cited in a given reference
 * :func:`query_ned_names`		- return multi-wavelength cross-IDs of a given target
 * :func:`query_ned_basic_posn`		- return basic position information on a given target
 * :func:`query_ned_external`		- return external web references to other databases 
                    for a given target
 * :func:`query_ned_allsky`		- return data for all-sky search criteria constraining 
                    redshift, position, fluxes, object type, survey
 * :func:`query_ned_photometry`		- return photometry for data on a given target
 * :func:`query_ned_diameters`		- return angular diameter data for a given target
 * :func:`query_ned_redshifts`		- return redshift data for a given target
 * :func:`query_ned_notes`		- return detailed notes on a given target
 * :func:`query_ned_position`		- return multi-wavelength position information on a 
                    given target
 * :func:`query_ned_nearpos`		- return data on objects on a cone search around given
                    position

Service URLs to acquire the VO Tables are taken from Mazzarella et al. (2007) 
	in The National Virtual Observatory: Tools and Techniques for Astronomical Research, 
	ASP Conference Series, Vol. 382., p.165

Note: two of the search functions described by Mazzarella et al. did not work as of June 2011:
	  * :func:`query_ned_basic` 		- retrieve basic data for an NED object
	  * :func:`query_ned_references`	- retrieve reference data for an NED object

Written by K. Willett, Jun 2011


Reference/API
=============

.. automodapi:: astroquery.ned
    :no-inheritance-diagram:
