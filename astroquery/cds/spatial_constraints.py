#!/usr/bin/env python
# -*- coding: utf-8 -*

# Licensed under a 3-clause BSD style license - see LICENSE.rst

from os import remove

from abc import abstractmethod, ABC

from regions import CircleSkyRegion
from regions import PolygonSkyRegion
from mocpy import MOC


class SpatialConstraint(ABC):
    """
    This abstract class provides an interface for spatial constraints

    The user can define a spatial constraint when querying
    the MOCServer. This class is an interface for different
    possible spatial constraints. Those are defined below
    such as CircleSkyRegionSpatialConstraint and
    PolygonSkyRegionSpatialConstraint
    """

    @abstractmethod
    def __init__(self, intersect):
        """
        SpatialConstraint's constructor

        Parameters:
        ----
        intersect : string
            specify if the defined region must overlaps,
            covers or encloses the mocs from each dataset
            stored in the MOCServer

        Exceptions:
        ----
        ValueError :
            - intersect must have its value in (overlaps, enclosed, covers)

        """
        self.__intersect = intersect
        self.request_payload = {'intersect': self.__intersect}

    @property
    def intersect(self):
        return self.__intersect

    @intersect.setter
    def intersect(self, value):
        if value not in ('overlaps', 'enclosed', 'covers'):
            print("intersect parameters must have a value in ('overlaps', 'enclosed', 'covers')")
            raise ValueError
        self.__intersect = value
        self.request_payload.update({'intersect': self.__intersect})

    # real signature unknown
    def __repr__(self, *args, **kwargs):
        result = "Spatial constraint having request payload :\n{0}".format(self.request_payload)
        return result


class Cone(SpatialConstraint):
    """
    Class defining a circle sky region

    Inherits from SpatialConstraint class
    and implements the cone search method

    """

    def __init__(self, circle_region, intersect='overlaps'):
        """
        CircleSkyRegionSpatialConstraint's constructor

        Parameters:
        ----
        circle_region : regions.CircleSkyRegion
            defines a circle of center(ra, dec) and radius given
            specifying the region in which one can ask for the datasets
            intersecting it

        Exceptions:
        ----
        TypeError:
            - circleSkyRegion must be of type regions.CircleSkyRegion

        """

        if not isinstance(circle_region, CircleSkyRegion):
            raise TypeError

        super(Cone, self).__init__(intersect)
        self.circle_region = circle_region
        self.request_payload.update({
            'DEC': circle_region.center.dec.to_string(decimal=True),
            'RA': circle_region.center.ra.to_string(decimal=True),
            'SR': str(circle_region.radius.value)
        })


class Polygon(SpatialConstraint):
    """
    Class defining a spatial polygon region

    Inherits from SpatialConstraint class
    and gives the user the possibility to defines
    a polygon as the region of interest for finding
    all the datasets intersecting it

    """

    def __init__(self, polygon_region, intersect='overlaps'):
        """
        PolygonSkyRegionSpatialConstraint's constructor

        Parameters:
        ----
        polygon_region : regions.PolygonSkyRegion
            defines a Polygon expressed as a list of vertices
            of type regions.SkyCoord

        Exceptions:
        ----
        TypeError :
            - polygonSkyRegion must be of type regions.PolygonSkyRegion

        AttributeError :
            - the SkyCoord referring to the vertices of the polygon
            needs to have at least 3 vertices otherwise it is
            not a polygon but a line or a single vertex

        """

        if not isinstance(polygon_region, PolygonSkyRegion):
            raise TypeError

        super(Polygon, self).__init__(intersect)

        # test if the polygon has at least 3 vertices
        if len(polygon_region.vertices.ra) < 3:
            print("A polygon must have at least 3 vertices")
            raise AttributeError

        self.request_payload.update({'stc' : self.__to_stc(polygon_region)})

    @staticmethod
    def __to_stc(polygon_region):
        """
        Convert a regions.PolygonSkyRegion instance to a string

        MOCServer requests for a polygon expressed in a STC format
        i.e. a string beginning with 'Polygon' and iterating through
        all the vertices' ra and dec

        """

        polygon_stc = "Polygon"
        for i in range(len(polygon_region.vertices.ra)):
            polygon_stc += ' ' + polygon_region.vertices.ra[i].to_string(decimal=True) + \
                           ' ' + polygon_region.vertices.dec[i].to_string(decimal=True)

        return polygon_stc


class Moc(SpatialConstraint):
    def __init__(self, intersect='overlaps'):
        """Contruct a constraint based on the surface covered by a moc"""
        self.request_payload = {}
        super(Moc, self).__init__(intersect)

    @classmethod
    def from_file(cls, filename, intersect='overlaps'):
        if not isinstance(filename, str):
            raise TypeError
        moc_constraint = cls(intersect=intersect)
        moc_constraint.request_payload.update({'moc': filename})
        return moc_constraint

    @classmethod
    def from_url(cls, url, intersect='overlaps'):
        if not isinstance(url, str):
            raise TypeError
        moc_constraint = cls(intersect=intersect)
        moc_constraint.request_payload.update({'url': url})
        return moc_constraint

    @classmethod
    def from_mocpy_object(cls, mocpy_obj, intersect='overlaps'):
        if not isinstance(mocpy_obj, MOC):
            raise TypeError

        import tempfile
        tmp_moc_file = tempfile.NamedTemporaryFile(delete=False)

        # dump the moc in json format in a temp file
        mocpy_obj.write(tmp_moc_file.name, format='json')
        # read it to retrieve the moc in json format
        with open(tmp_moc_file.name, 'r') as f_in:
            content = f_in.read()

        # finally delete the temp file
        import os
        os.unlink(tmp_moc_file.name)

        moc_constraint = cls(intersect=intersect)
        moc_constraint.request_payload.update({'moc': content})
        return moc_constraint
