# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""CDS MOCServer Query Tool.
----------------------------

:Author: Matthieu Baumann (matthieu.baumann@astro.unistra.fr)

This package is for querying the CDS MOC service, primarily hosted at:

* http://alasky.unistra.fr/MocServer/query
* http://alaskybis.unistra.fr/MocServer/query (mirror)

Note: If the access to MOCs with the MOCServer tool was helpful for your research,
the following acknowledgment would be appreciated::

  This research has made use of the MOCServer, a tool developed at CDS, Strasbourg,
  France aiming at retrieving MOCs/meta-data from known data-sets. MOC is an IVOA
  standard described in :
  http://www.ivoa.net/documents/MOC/20140602/REC-MOC-1.0-20140602.pdf
"""

# Licensed under a 3-clause BSD style license - see LICENSE.rst

from astropy import config as _config


class Conf(_config.ConfigNamespace):
    """Configuration parameters for ``astroquery.template_module``."""

    server = _config.ConfigItem(
        [
            "https://alasky.unistra.fr/MocServer/query",
            "https://alaskybis.unistra.fr/MocServer/query",
        ],
        "Name of the template_module server to use.",
    )

    timeout = _config.ConfigItem(
        30, "Time limit for connecting to template_module server."
    )

    default_fields = [
        "ID",
        "obs_title",
        "obs_description",
        "nb_rows",
        "obs_regime",
        "bib_reference",
        "dataproduct_type",
    ]


conf = Conf()

from .core import MOCServer, MOCServerClass

__all__ = ["Conf", "conf", "MOCServer", "MOCServerClass"]
