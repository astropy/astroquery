# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
=======================
PLATO Astroquery Module
=======================

European Space Astronomy Centre (ESAC)
European Space Agency (ESA)

"""
from astroquery.utils import commons

from . import conf
import astroquery.esa.utils.utils as esautils
import astropy.units as u

__all__ = ['Plato', 'PlatoClass']


class PlatoClass(esautils.EsaTap):

    """
    This module connects with ESA Plato TAP
    """

    ESA_ARCHIVE_NAME = "PLATO"
    TAP_URL = conf.PLATO_TAP_SERVER
    LOGIN_URL = conf.PLATO_LOGIN_SERVER
    LOGOUT_URL = conf.PLATO_LOGOUT_SERVER

    def search_catalogue(self, table_name, *, target_name=None, coordinates=None, radius=1*u.arcmin, columns=None,
                         get_metadata=False, output_file=None, **filters):
        """
        Execute a search in one of the catalogues and associated tbles available in PLATO TAP.

        Parameters
        ----------
        table_name: str, mandatory
            Table name of the catalogue to be searched
        target_name: str, optional
            Name of the target to be resolved against SIMBAD/NED/VIZIER
        coordinates: str or SkyCoord, optional
            coordinates of the center in the cone search
        radius: float or quantity, optional, default value 14 degrees
            radius in degrees (int, float) or quantity of the cone_search
        columns : str or list of str, optional, default None
            Columns from the table to be retrieved. They can be checked using
            get_metadata=True
        get_metadata : bool, optional, default False
            Get the table metadata to verify the columns that can be filtered
        output_file : str, optional, default None
            file name where the results are saved.
            If this parameter is not provided, the jobid is used instead
        **filters : str, optional, default None
            Filters to be applied to the search. The column name is the keyword and the value is any
            value accepted by the column datatype. They will be
            used to generate the SQL filters for the query. Some examples are described below,
            where the left side is the parameter defined for this method and the right side the
            SQL filter generated:
            StarName='star1' -> StarName = 'star1'
            StarName='star*' -> StarName ILIKE 'star%'
            StarName='star%' -> StarName ILIKE 'star%'
            StarName=['star1', 'star2'] -> StarName = 'star1' OR StarName - 'star2'
            ra=('>', 30) -> ra > 30
            ra=(20, 30) -> ra >= 20 AND ra <= 30

        Returns
        -------
        An astropy.table object containing the results of the filters in the PIC target catalogue
        """
        cone_search_filter = None
        if radius is not None:
            radius = esautils.get_degree_radius(radius)

        if target_name and coordinates:
            raise TypeError("Please use only target or coordinates as "
                            "parameter.")
        elif target_name:
            coordinates = esautils.resolve_target(conf.PLATO_TARGET_RESOLVER,
                                                  self.tap._session, target_name,
                                                  'ALL')
            cone_search_filter = self.create_cone_search_query(coordinates.ra.deg, coordinates.dec.deg,
                                                               "RAdeg", "DEdeg", radius)
        elif coordinates:
            coord = commons.parse_coordinates(coordinates=coordinates)
            ra = coord.ra.degree
            dec = coord.dec.degree
            cone_search_filter = self.create_cone_search_query(ra, dec, "RAdeg", "DEdeg", radius)

        return self.query_table(table_name=table_name, columns=columns,
                                custom_filters=cone_search_filter, get_metadata=get_metadata, async_job=True,
                                output_file=output_file, **filters)

    def search_pic_target_go(self, *, target_name=None, coordinates=None, radius=1*u.arcmin, columns=None,
                             get_metadata=False, output_file=None, **filters):
        """
        Execute a search in PIC Target Catalogue.

        Parameters
        ----------
        target_name: str, optional
            Name of the target to be resolved against SIMBAD/NED/VIZIER
        coordinates: str or SkyCoord, optional
            coordinates of the center in the cone search
        radius: float or quantity, optional, default value 14 degrees
            radius in degrees (int, float) or quantity of the cone_search
        columns : str or list of str, optional, default None
            Columns from the table to be retrieved. They can be checked using
            get_metadata=True
        get_metadata : bool, optional, default False
            Get the table metadata to verify the columns that can be filtered
        output_file : str, optional, default None
            file name where the results are saved.
            If this parameter is not provided, the jobid is used instead
        **filters : str, optional, default None
            Filters to be applied to the search. The column name is the keyword and the value is any
            value accepted by the column datatype. They will be
            used to generate the SQL filters for the query. Some examples are described below,
            where the left side is the parameter defined for this method and the right side the
            SQL filter generated:
            StarName='star1' -> StarName = 'star1'
            StarName='star*' -> StarName ILIKE 'star%'
            StarName='star%' -> StarName ILIKE 'star%'
            StarName=['star1', 'star2'] -> StarName = 'star1' OR StarName - 'star2'
            ra=('>', 30) -> ra > 30
            ra=(20, 30) -> ra >= 20 AND ra <= 30

        Returns
        -------
        An astropy.table object containing the results of the filters in the PIC target catalogue
        """

        return self.search_catalogue(table_name='pic_go.pic_target_go', target_name=target_name,
                                     coordinates=coordinates, radius=radius, columns=columns,
                                     get_metadata=get_metadata, output_file=output_file, **filters)

    def search_pic_contaminant_go(self, *, target_name=None, coordinates=None, radius=1*u.arcmin, columns=None,
                                  get_metadata=False, output_file=None, **filters):
        """
        Execute a search in PIC Contaminant Catalogue.

        Parameters
        ----------
        target_name: str, optional
            Name of the target to be resolved against SIMBAD/NED/VIZIER
        coordinates: str or SkyCoord, optional
            coordinates of the center in the cone search
        radius: float or quantity, optional, default value 14 degrees
            radius in degrees (int, float) or quantity of the cone_search
        columns : str or list of str, optional, default None
            Columns from the table to be retrieved. They can be checked using
            get_metadata=True
        get_metadata : bool, optional, default False
            Get the table metadata to verify the columns that can be filtered
        output_file : str, optional, default None
            file name where the results are saved.
            If this parameter is not provided, the jobid is used instead
        **filters : str, optional, default None
            Filters to be applied to the search. The column name is the keyword and the value is any
            value accepted by the column datatype. They will be
            used to generate the SQL filters for the query. Some examples are described below,
            where the left side is the parameter defined for this method and the right side the
            SQL filter generated:
            StarName='star1' -> StarName = 'star1'
            StarName='star*' -> StarName ILIKE 'star%'
            StarName='star%' -> StarName ILIKE 'star%'
            StarName=['star1', 'star2'] -> StarName = 'star1' OR StarName - 'star2'
            ra=('>', 30) -> ra > 30
            ra=(20, 30) -> ra >= 20 AND ra <= 30

        Returns
        -------
        An astropy.table object containing the results of the filters in the PIC target catalogue
        """

        return self.search_catalogue(table_name='pic_go.pic_contaminant_go', target_name=target_name,
                                     coordinates=coordinates, radius=radius, columns=columns,
                                     get_metadata=get_metadata, output_file=output_file, **filters)

    def plot_plato_results(self, x, y, x_label, y_label, plot_title, *, z=None, z_label=None, error_x=None,
                           error_y=None, log_scale=False, color='gray', fig=None, ax=None):
        """
        Draw two columns in a 2D plot with/without a third column drawn with a colormap
        Parameters
        ----------
        x : array of numbers, mandatory
            values for the X series
        y : array of numbers, mandatory
            values for the Y series
        x_label : str, mandatory
            title of the X axis
        y_label : str, mandatory
            title of the Y axis
        plot_title : str, mandatory
            title of the plot
        z : array of numbers, optional
            values to assign a color to each dot
        z_label : str, optional
            title of the colormap
        error_x : array of numbers, optional
            error on the X series
        error_y : array of numbers, optional
            error on the Y series
        log_scale : boolean, optional, default False
            Draw X and Y axes using log scale
        color : str, optional, default gray
            Color to be used in the 2D plot or a colormap if Z axis is defined
        fig : matplotlib.figure.Figure, optional
            Existing figure to draw on. If None, a new figure is created.
        ax : matplotlib.axes.Axes, optional
            Existing axes to draw on. If None, a new axes object is created.

        Returns
        -------
        fig : matplotlib.figure.Figure
            The figure containing the plot.
        ax : matplotlib.axes.Axes
            The axes object used for plotting.
        """

        # Matplotlib is needed to execute this method
        try:
            import matplotlib.pyplot as plt
            # Enable interactive mode
            plt.ion()
        except ImportError:
            raise ImportError(
                "This feature requires 'matplotlib' library. "
                "Install it with: pip install matplotlib"
            )

        if fig is None or ax is None:
            fig, ax = plt.subplots()

            # Draw the PLATO logo in the image
            try:
                logo = esautils.load_image_from_url(conf.PLATO_LOGO)
                logo = logo.convert("RGBA")
                # Create a small axes for the image (figure coordinates! Not data)
                logo_ax = fig.add_axes((0.89, 0.85, 0.15, 0.15), anchor='NW')
                logo_ax.imshow(logo)
                logo_ax.axis("off")
            except Exception:
                pass  # If the image cannot be loaded, just ignore it

        # Error bars behind the data series
        if error_x is not None or error_y is not None:
            ax.errorbar(
                x, y,
                xerr=error_x,
                yerr=error_y,
                fmt='none',
                ecolor='black',
                capsize=2,
                zorder=2
            )

        # Scatter plot with the selected data (2 or 3 lists)
        if z is not None:
            sc = ax.scatter(x, y, c=z, cmap=color, zorder=3)
            cbar = fig.colorbar(sc, ax=ax)
            if z_label:
                cbar.set_label(z_label)
        else:
            ax.scatter(x, y, color=color, zorder=3)

        # Labels, scale and title
        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)

        if log_scale:
            ax.set_xscale('log')
            ax.set_yscale('log')

        if 'RA (deg)' in x_label:
            ax.invert_xaxis()

        ax.set_title(plot_title)

        plt.show(block=False)

        return fig, ax


Plato = PlatoClass()
