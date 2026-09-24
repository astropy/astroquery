# -*- coding: utf-8 -*-
# Licensed under a 3-clause BSD style license - see LICENSE.rst
#
# Astropy documentation build configuration file.
#
# This file is execfile()d with the current directory set to its containing dir.
#
# Note that not all possible configuration values are present in this file.
#
# All configuration values have a default. Some values are defined in
# the global Astropy configuration which is loaded here before anything else.
# See astropy.sphinx.conf for which values are set there.

import datetime
import sys

if sys.version_info < (3, 11):
    import tomli as tomllib
else:
    import tomllib

from pathlib import Path

import requests
from matplotlib import pyplot as plt
from matplotlib.sphinxext import plot_directive
from pyvo.dal.exceptions import DALServiceError, DALQueryError
from sphinx.util import logging as sphinx_logging

from astroquery.exceptions import RemoteServiceError, TimeoutError as AQTimeoutError

# Load all of the global Astropy configuration
try:
    from sphinx_astropy.conf.v3 import *  # noqa
except ImportError:
    print('ERROR: the documentation requires the sphinx-astropy package to '
          'be installed')
    sys.exit(1)

# Get configuration information from pyproject.toml
with (Path(__file__).parents[1] / 'pyproject.toml').open('rb') as fh:
    project_meta = tomllib.load(fh)['project']

# -- General configuration ----------------------------------------------------

# If your documentation needs a minimal Sphinx version, state it here.
# needs_sphinx = '1.2'

# To perform a Sphinx version check that needs to be more specific than
# major.minor, call `check_sphinx_version("x.y.z")` here.
# check_sphinx_version("1.2.1")

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
exclude_patterns.append('_templates')
exclude_patterns.append('release_not*')

# This is added to the end of RST files - a good place to put substitutions to
# be used globally.
rst_epilog += """
"""

del intersphinx_mapping['scipy']
del intersphinx_mapping['h5py']

intersphinx_mapping.update({
    'requests': ('https://requests.kennethreitz.org/en/stable', None),
    'regions': ('https://astropy-regions.readthedocs.io/en/stable', None),
    'mocpy': ('https://cds-astro.github.io/mocpy', None),
    'pyvo': ('https://pyvo.readthedocs.io/en/stable', None),
})

# -- Project information ------------------------------------------------------

# This does not *have* to match the package name, but typically does
project = project_meta['name']
author = project_meta['authors'][0]['name']
copyright = f'2011-{datetime.datetime.now(datetime.timezone.utc).year}, {author}'

# The version info for the project you're documenting, acts as replacement for
# |version| and |release|, also used in various other places throughout the
# built documents.

__import__(project)
package = sys.modules[project]

# The short X.Y version.
version = package.__version__.split('-', 1)[0]
# The full version, including alpha/beta/rc tags.
release = package.__version__


# -- Options for HTML output ---------------------------------------------------

# Add any paths that contain custom themes here, relative to this directory.
# To use a different custom theme, add the directory containing the theme.
# html_theme_path = []

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes. To override the custom theme, set this to the
# name of a builtin theme or the name of a custom theme in html_theme_path.
# html_theme = None

# Custom sidebar templates, maps document names to template names.
# html_sidebars = {}

# The name of an image file (within the static path) to use as favicon of the
# docs.  This file should be a Windows icon file (.ico) being 16x16 or 32x32
# pixels large.
# html_favicon = ''

# If not '', a 'Last updated on:' timestamp is inserted at every page bottom,
# using the given strftime format.
# html_last_updated_fmt = ''

# The name for this set of Sphinx documents.  If None, it defaults to
# "<project> v<release> documentation".
html_title = '{0} v{1}'.format(project, release)

# Output file base name for HTML help builder.
htmlhelp_basename = project + 'doc'

html_theme_options = {
    "logo": {
        "image_light": "_static/astroquery_logo_light.svg",
        "image_dark": "_static/astroquery_logo_dark.svg",
    }
}

# -- Options for LaTeX output --------------------------------------------------

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title, author, documentclass [howto/manual]).
latex_documents = [('index', project + '.tex', project + u' Documentation',
                    author, 'manual')]


# -- Options for manual page output --------------------------------------------

# One entry per manual page. List of tuples
# (source start file, name, description, authors, manual section).
man_pages = [('index', project.lower(), project + u' Documentation',
              [author], 1)]


# Setting this URL is requited by sphinx-astropy
github_issues_url = 'https://github.com/astropy/astroquery/issues/'
nitpicky = True
nitpick_ignore = [('py:class', 'astroquery.mast.core.MastQueryWithLogin'),
                  # astropy interited type annotations
                  ('py:class', 'ConfigItem')]


# -- Linkcheck builder options ----------------------------------------------
#
linkcheck_retry = 3
linkcheck_ignore = [
    'https://mast.stsci.edu/search/ui/#', # these anchors don't work with linkcheker
    'https://nxsa.esac.esa.int/nxsa-web/#aio',
    'https://ssd.jpl.nasa.gov/horizons/manual.html#center',
    'https://splatalogue.online/#/basic',
    'https://ui.adsabs.harvard.edu',  # 405 Client Error: Not Allowed for sphinx-build
]


# -- Plot directive: tolerate remote service outages --------------------------
#
# Some ``.. plot::`` blocks query live services (e.g. IRSA, CDMS). With warnings
# treated as errors, a temporary outage of any of those services would fail the
# whole docs build. Instead, when a plot fails because of a remote-service or
# network error, render a placeholder figure and log it without a warning.

_REMOTE_ERRORS = (requests.exceptions.RequestException, ConnectionError, TimeoutError,
                  DALServiceError, DALQueryError, RemoteServiceError, AQTimeoutError)
_plot_logger = sphinx_logging.getLogger(__name__)


def _run_code_tolerating_outages(run_code):
    def wrapper(code, code_path, *args, **kwargs):
        try:
            return run_code(code, code_path, *args, **kwargs)
        except plot_directive.PlotError as err:
            if not isinstance(err.__cause__, _REMOTE_ERRORS):
                raise
            _plot_logger.info(f"Remote service unavailable while running a plot in "
                              f"{code_path}; rendering a placeholder figure instead.\n"
                              f"{type(err.__cause__).__name__}: {err.__cause__}")
            plt.close('all')
            fig = plt.figure(figsize=(6, 1.5))
            fig.text(0.5, 0.5, "Figure not rendered: a remote service was unavailable\n"
                     "when this documentation was built.", ha='center', va='center')
            return {}
    return wrapper


# ``_run_code`` is private matplotlib API (``run_code`` before 3.9); if it is
# missing, plots simply behave as before.
for _name in ('_run_code', 'run_code'):
    if hasattr(plot_directive, _name):
        setattr(plot_directive, _name, _run_code_tolerating_outages(getattr(plot_directive, _name)))
        break
