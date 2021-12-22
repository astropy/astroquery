.. doctest-skip-all

.. _astroquery.esa.neocc:

***********************************************************************************************
ESA NEOCC Portal Python Interface Library (`astroquery.esa.neocc`/astroquery.solarsystem.neocc)
***********************************************************************************************

The ESA NEO Coordination Centre (NEOCC) is the operational centre of ESA’s Planetary Defence Office
PDO) within the Space Safety Programme (S2P). Its aim is to coordinate and contribute to the
observation of small Solar System bodies in order to evaluate and monitor the threat coming from 
near-Earth objects (NEOs).

ESA NEOCC Portal Python interface library makes the data that `ESA NEOCC <https://neo.ssa.esa.int/>`_
provides easily accessible through a Python program.

The main functionality of this library is to allow a programmer to easily retrieve:

* All the NEAs
* Other data that the NEOCC provides (risk list, close approach list, etc.)
* All basic and advanced information regarding a NEA
* An ephemeris service for NEAs

==============================
Getting ESA NEOCC's products
==============================

--------------------------------
1. Direct download of list files
--------------------------------
This function allows the user to download the requested list data from ESA NEOCC.
Different lists that can be requested are:

* All NEA list: *nea_list*
* Catalogue of NEAs (current date): *neo_catalogue_current*
* Catalogue of NEAs (middle arc): *neo_catalogue_middle*
* Updated NEA list: *updated_nea*
* Monthly computation date: *monthly_update*
* Risk list (normal): *risk_list*
* Risk list (special): *risk_list_special*
* Close approaches (upcoming): *close_approaches_upcoming*
* Close approaches (recent): *close_approaches_recent*
* Priority list (normal): *priority_list*
* Priority list (faint): *priority_list_faint*
* Close encounter list: *close_encounter*
* Impacted objects: *impacted_objects*
 
These lists are referenced in `<https://neo.ssa.esa.int/computer-access>`_.
--------------------------------
Examples
--------------------------------
**NEA list, Updated NEA list, Monthly computation date:** The output
of this list is a *pandas.Series* which contains the list of all NEAs
currently considered in the NEOCC system.

.. code-block:: python

    >>> from astroquery.esa.neocc import neocc
    >>> list_data = neocc.query_list(list_name='nea_list')
    >>> list_data
    0            433 Eros
    1          719 Albert
    2          887 Alinda
    3        1036 Ganymed
    4           1221 Amor
                ...
    25191          2021DY
    25192         2021DY1
    25193          2021DZ
    25194         2021DZ1
    25195         6344P-L
    Name: 0, Length: 25196, dtype: object

Each asteroid can be accessed using its index. This information can
be used as input for *query_object* method.

.. code-block:: python

    >>> list_data[4]
    '1221 Amor'

**Other lists:**  The output of this list is a *pandas.DataFrame* which
contains the information of the requested list.

.. code-block:: python

    >>> from astroquery.esa.neocc import neocc
    >>> list_data = neocc.query_list(list_name='close_approaches_upcoming')
    >>> list_data
            Object Name         Date   ...   Rel. vel in km/s
    0             2021DE  2021.156164  ...                26.0
    1             2021DM  2021.158904  ...                10.2
    2             2011DW  2021.161644  ...                13.6
    3           2011EH17  2021.161644  ...                16.8
    4            2016DV1  2021.164384  ...                18.6
    ..               ...          ...  ...                 ...
    141           2020DF  2022.120548  ...                 8.6
    142          2018CW2  2022.131507  ...                10.8
    143          2020CX1  2022.131507  ...                 8.2
    144  455176 1999VF22  2022.142466  ...                25.1
    145          2017CX1  2022.145205  ...                 5.0
    [146 rows x 10 columns]

The information of the columns can be accessed through (see
`pandas <https://pandas.pydata.org/pandas-docs/stable/index.html>`_
for further information about data access):

.. code-block:: python

    >>> list_data['Object Name']
    0               2021DE
    1               2021DM
    2               2011DW
    3             2011EH17
    4              2016DV1
                ...
    141             2020DF
    142            2018CW2
    143            2020CX1
    144    455176 1999VF22
    145            2017CX1
    Name: Object Name, Length: 146, dtype: object

And the information of the rows can be accessed using:

.. code-block:: python

    >>> list_data.iloc[2]
    Object Name              2011DW
    Date                    2021.16
    Miss Distance in km     5333057
    Miss Distance in au    0.035649
    Miss Distance in LD      13.874
    Diameter in m                90
    *=Yes                         *
    H                          22.9
    Max Bright                 16.4
    Rel. vel in km/s           13.6
    Name: 2, dtype: object

**Note:** If the contents request fails the following message will be printed:

*Initial attempt to obtain list failed. Reattempting...*

Then a second request will be automatically sent to the NEOCC portal.

---------------------------------------
2. Direct download of data on an object
---------------------------------------

This function allows the user to download the requested data for the object designated.
The information that can be requested is the one shown in the relevant tabs for each object from
ESA NEOCC. The list of tabs that can be requested is:

* Asteroid orbit properties: *orbit_properties*
* Asteroid physical properties: *physical_properties*
* Asteroid observation records: *observations*
* Generation of observational ephemerides for an object: *ephemerides*
* Asteroid close approach report: *close_approaches*
* Possible impacts: *impacts*

These tabs are referenced in `<https://neo.ssa.esa.int/computer-access>`_.
--------------------------------
Examples
--------------------------------
**Impacts, Physical Properties and Observations**: This example
tries to summarize how to access the data of this tabs and how to
use it. Note that this classes only require as inputs the name of
the object and the requested tab.

The information can be obtained introducing directly the name of
the object, but it can be also added from the output of a
*query_list* search:

.. code-block:: python

    >>> from astroquery.esa.neocc import neocc
    >>> ast_impacts = neocc.query_object(name='1979XB', tab='impacts')

or

.. code-block:: python

    >>> nea_list = neocc.query_list(list_name='nea_list')
    >>> nea_list[2921]
    '1979XB'
    >>> ast_impacts = neocc.query_object(name=nea_list[2921], tab='impacts')

or

.. code-block:: python

    >>> risk_list = neocc.query_list(list_name='risk_list')
    >>> risk_list['Object Name'][1]
    '1979XB'
    >>> ast_impacts = neocc.query_object(name=risk_list['Object Name'][1],
                                        tab='impacts')

The output provides an object with the different attributes:

.. code-block:: python

    >>> ast_impacts.<tab>
    ast.additional_note       ast.impacts
    ast.arc_end               ast.info
    ast.arc_start             ast.observation_accepted
    ast.computation           ast.observation_rejected

By adding the attribute its information can be accessed:

.. code-block:: python

    >>> ast_impacts.impacts
                date        MJD  sigma  ...  Exp. Energy in MT    PS  TS
    0  2056-12-12.902  72344.902  0.255  ...           0.011500 -3.22   0
    1  2065-12-16.462  75635.463 -1.110  ...           0.000090 -5.36   0
    2  2086-12-16.663  83305.664 -1.101  ...           0.002390 -4.03   0
    3  2101-12-14.203  88781.204 -0.384  ...           0.000131 -5.36   0
    4  2105-12-12.764  90240.765  1.003  ...           0.000574 -4.75   0
    5  2113-12-14.753  93164.753 -0.706  ...           0.018500 -3.25   0
    6  2113-12-14.756  93164.756 -0.708  ...           0.000163 -5.30   0
    7  2117-12-15.496  94626.496 -1.316  ...           0.000069 -5.68   0
    [8 rows x 11 columns]

**Note:** Most of the dataframes of the object tabs contain the
'help' property which contains information about the fields
of the dataframe.

.. code-block:: python

    >>> print(ast_impacts.impacts.help)
    Data frame with possible impacts information:
    -Date: date for the potential impact in YYYY-MM-DD.ddd format
    -MJD: Modified Julian Day for the potential impact
    -sigma: approximate location along the Line Of Variation (LOV)
    in sigma space
    -sigimp: The lateral distance in sigma-space from the LOV to
    the Earth surface. A zero implies that the LOV passes through
    the Earth-dist: Minimum Distance in Earth radii. The lateral
    distance from the LOV to the centre of the Earth
    -width: one-sigma semi-width of the Target Plane confidence
    region in Earth radii
    -stretch: Stretching factor. It indicates how much the
    confidence region at the epoch has been stretched by the time
    of the approach. This is a close cousin of the Lyapounov
    exponent. Units are in Earth radii divided by sigma (RE/sig)
    -p_RE: probability of Earth Impact (IP)
    -Exp. Energy in MT: Expected energy. It is the product of the
    impact energy and the impact probability
    -PS: Palermo Scale
    -TS: Torino Scale

Another example is shown to obtain the physical properties:

.. code-block:: python

    >>> from astroquery.esa.neocc import neocc
    >>> properties = neocc.query_object(name='433', tab='physical_properties')

Again, the output provides an object with different attributes:

.. code-block:: python

    >>> properties.<tab>
    properties.physical_properties  properties.sources
    >>> properties.physical_properties
                    Property                  Value(s)                 Units              Reference(s)
    0           Rotation Period                      5.27                     h                       [4]
    1                   Quality                       4.0                     -                       [4]
    2                 Amplitude                 0.04-1.49                   mag                       [4]
    3        Rotation Direction                       PRO                     -                       [1]
    4              Spinvector L                      16.0                   deg                       [1]
    5              Spinvector B                       9.0                   deg                       [1]
    6                  Taxonomy                        Sq                     -                       [2]
    7            Taxonomy (all)                         S                     -                       [3]
    8    Absolute Magnitude (H)           [10.853, 10.31]            [mag, mag]                [[5], [6]]
    9       Slope Parameter (G)     [0.46**, 0.2, 0.46**]       [mag, mag, mag]           [[7], [8], [5]]
    10                   Albedo                      0.24                     -                       [9]
    11                 Diameter                   23300.0                     m                      [10]
    12  Color Index Information  [0.85, 0.48, 0.39, 0.52]  [B-V, V-R, R-I, U-B]  [[11], [11], [11], [12]]
    13                Sightings       [Radar R, Visual S]                [-, -]              [[13], [14]]


**Note:** For the case of tab Observations there are objects which contain
"Roving observer" and satellite observations. In the original
requested data the information of these observations produces two
lines of data, where the second line does not fit the structure of
the data frame
(https://www.minorplanetcenter.org/iau/info/OpticalObs.html).
In order to solve this problem those second lines
have been extracted in another attribute (e.g. sat_observations or
roving_observations) to make the data more readable.

Since this information can be requested in pairs, i.e. it is needed
to access both lines of data, this can be made using the date of the
observations which will be the same for both attributes:

.. code-block:: python

    >>> ast_observations = neocc.query_object(name='99942',
    tab='observations')
    >>> sat_obs = ast_observations.sat_observations
    >>> sat_obs
        Design.  K  T  N  YYYY  MM  DD.dddddd  ... Obs Code
    0     99942  S  s     2020  12   18.97667  ...      C51
    1     99942  S  s     2020  12   19.10732  ...      C51
    ...     ...            ...            ...  ...      ...
    10    99942  S  s     2021   1   16.92315  ...      C53
    11    99942  S  s     2021   1   19.36233  ...      C53
    12    99942  S  s     2021   1   19.36927  ...      C53
    >>> opt_obs = ast_ast_observations.optical_observations
    >>> opt_obs.loc[opt_obs['DD.dddddd'] == sat_obs['DD.dddddd'][0]]
            Design.  K  T N  YYYY  MM  ...  Obs Code   Chi  A  M
    4582    99942    S  S    2020  12  ...       C51  1.13  1  1
    [1 rows x 33 columns]

**Close Approaches**: This example corresponds to the class close
approaches. As for the previous example, the information can be
obtained by directly introducing the name of the object or from a
previous *query_list* search.

In this particular case, there are no attributes and the data obtained is
a DataFrame which contains the information for close approaches:

.. code-block:: python

    >>> close_appr = neocc.query_object(name='99942', tab='close_approaches')
    >>> close_appr
        BODY     CALENDAR-TIME  ...         WIDTH  PROBABILITY
    0   EARTH  1957/04/01.13908  ...  1.318000e-08        1.000
    1   EARTH  1964/10/24.90646  ...  1.119000e-08        1.000
    2   EARTH  1965/02/11.51118  ...  4.004000e-09        1.000
    ...   ...               ...  ...           ...          ...
    16  EARTH  2080/05/09.23878  ...  1.206000e-06        0.821
    17  EARTH  2087/04/07.54747  ...  1.254000e-08        0.327
    [18 rows x 10 columns]

**Orbit Properties:** In order to access the orbit properties
information, it is necessary to provide two additional inputs to
*query_object* method: **orbital_elements** and **orbit_epoch**.

It is mandatory to write these two parameters as: *orbit_epoch=' '*
to make the library works.

.. code-block:: python

    >>> ast_orbit_prop = neocc.query_object(name='99942',
    tab='orbit_properties',orbital_elements='keplerian', orbit_epoch='present')
    >>> ast_orbit_prop.<tab>
    ast_orbit_prop.anode       ast_orbit_prop.ngr
    ast_orbit_prop.aphelion    ast_orbit_prop.orb_type
    ast_orbit_prop.cor         ast_orbit_prop.perihelion
    ast_orbit_prop.cov         ast_orbit_prop.period
    ast_orbit_prop.dnode       ast_orbit_prop.pha
    ast_orbit_prop.epoch       ast_orbit_prop.rectype
    ast_orbit_prop.form        ast_orbit_prop.refsys
    ast_orbit_prop.kep         ast_orbit_prop.rms
    ast_orbit_prop.lsp         ast_orbit_prop.u_par
    ast_orbit_prop.mag         ast_orbit_prop.vinfty
    ast_orbit_prop.moid

**Ephemerides:** In order to access ephemerides information, it
is necessary to provide five additional inputs to *query_object*
method: **observatory**, **start**, **stop**, **step** and
**step_unit***.

It is mandatory to write these five parameters as: *observatory=' '*
to make the library works.

.. code-block:: python

    >>> ast_ephemerides = neocc.query_object(name='99942',
    tab='ephemerides', observatory='500', start='2019-05-08 01:30',
    stop='2019-05-23 01:30', step='1', step_unit='days')
    >>> ast_ephemerides.<tab>
    ast_ephemerides.ephemerides  ast_ephemerides.tinit
    ast_ephemerides.observatory  ast_ephemerides.tstep
    ast_ephemerides.tfinal

==============================
How to export data
==============================

-------------------
1. To JSON
-------------------

Most of the data obtained from ESA NEOCC Python Interface is collected as *pandas.Series* or *pandas.DataFrame* and, therefore
it can be easily converted to JSON format. Here is a template that you may use in Python to export pandas DataFrame to JSON:

.. code-block:: python

    >>> df.to_json(r'Path to store the exported JSON file\File Name.json')

The complete use of this function can be found in `pandas.DataFrame.to_json <https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.to_json.html>`_, 
where different examples are shown. It also shows how to obtain the different types of JSON files.

.. code-block:: python

    >>> from astroquery.esa.neocc import neocc
    >>> import json
    >>> ast = neocc.query_object(name='99942', tab='physical_properties')
    >>> ast.physical_properties
                      Property    Values Unit Source
    0           Rotation Period     30.56    h    [4]
    1                   Quality         3    -    [4]
    2                 Amplitude       1.0  mag    [4]
    3        Rotation Direction     RETRO    -    [1]
    4              Spinvector L       250  deg    [1]
    5              Spinvector B   -7.50E1  deg    [1]
    6                  Taxonomy      S/Sq    -    [2]
    7            Taxonomy (all)  Sq,Scomp    -    [3]
    8    Absolute Magnitude (H)     19.09  mag    [5]
    9       Slope Parameter (G)      0.24  mag    [1]
    10                   Albedo     0.285    -    [8]
    11                 Diameter       375    m    [9]
    12  Color Index Information     0.362  R-I   [10]
    13                Sightings   Radar R    -   [11]
    >>> ast_json = ast.physical_properties.to_json(orient='split')
    >>> parsed = json.loads(ast_json)
    >>> print(json.dumps(parsed, indent=4))
    {
        "columns": [
            "Property",
            "Values",
            "Unit",
            "Source"
        ],
        "index": [
            0,
            1,
            2,
            3,
            4,
            5,
            6,
            7,
            8,
            9,
            10,
            11,
            12,
            13
        ],
        "data": [
            [
                "Rotation Period",
                "30.56",
                "h",
                "[4]"
            ],
            [
                "Quality",
                "3",
                "-",
                "[4]"
            ],
            [
                "Amplitude",
                "1.0",
                "mag",
                "[4]"
            ],
            [
                "Rotation Direction",
                "RETRO",
                "-",
                "[1]"
            ],    
            [
                "Spinvector L",
                "250",
                "deg",
                "[1]"
            ],
            [
                "Spinvector B",
                "-7.50E1",
                "deg",
                "[1]"
            ],
            [    
                "Taxonomy",
                "S/Sq",
                "-",
                "[2]"
            ],
            [    
                "Taxonomy (all)",
                "Sq,Scomp",
                "-",
                "[3]"
            ],
            [
                "Absolute Magnitude (H)",
                "19.09",
                "mag",
                "[5]"
            ],
            [
                "Slope Parameter (G)",
                "0.24",
                "mag",
                "[1]"
            ],
            [
                "Albedo",
                "0.285",
                "-",
                "[8]"
            ],
            [
                "Diameter",
                "375",
                "m",
                "[9]"
            ],
            [
                "Color Index Information",
                "0.362",
                "R-I",
                "[10]"
            ],
            [    
                "Sightings",
                "Radar R",
                "-",
                "[11]"
            ]
        ]
    }
    >>> ast_json = ast.physical_properties.to_json(r'Path to store the exported JSON file/ast.json',orient='split')

----------------------
2. To Tables (VO Tables)
----------------------

Virtual Observatory (VO) tables are a new format developed by the International Virtual Observatory Alliance to store one or more tables. 
This format is included within `ATpy <https://atpy.readthedocs.io/en/stable/index.html>`_ library. However, most of ATpy’s functionalities has now been incorporated 
into Astropy library and the developers recommended to use the `Astropy Tables <https://docs.astropy.org/en/stable/table/>`_

Astropy documentation details how to interface with the Pandas library, i.e., how to convert data in *pandas.Series* or *pandas.DataFrame* formats into Astropy Tables and vice versa.

.. code-block:: python

    >>> from astroquery.esa.neocc import neocc
    >>> from astropy.table import Table
    >>> ast = neocc.query_object(name='99942', tab='physical_properties')
    >>> ast.physical_properties
                      Property    Values Unit Source
    0           Rotation Period     30.56    h    [4]
    1                   Quality         3    -    [4]
    2                 Amplitude       1.0  mag    [4]
    3        Rotation Direction     RETRO    -    [1]
    4              Spinvector L       250  deg    [1]
    5              Spinvector B   -7.50E1  deg    [1]
    6                  Taxonomy      S/Sq    -    [2]
    7            Taxonomy (all)  Sq,Scomp    -    [3]
    8    Absolute Magnitude (H)     19.09  mag    [5]
    9       Slope Parameter (G)      0.24  mag    [1]
    10                   Albedo     0.285    -    [8]
    11                 Diameter       375    m    [9]
    12  Color Index Information     0.362  R-I   [10]
    13                Sightings   Radar R    -   [11]
    >>> ast_astropy = Table.from_pandas(ast.physical_properties)
    >>> ast_astropy
    <Table length=14>
            Property         Values  Unit Source
             str23            str8   str3  str4 
    ----------------------- -------- ---- ------
            Rotation Period    30.56    h    [4]
                    Quality        3    -    [4]
                  Amplitude      1.0  mag    [4]
         Rotation Direction    RETRO    -    [1]
               Spinvector L      250  deg    [1]
               Spinvector B  -7.50E1  deg    [1]
                   Taxonomy     S/Sq    -    [2]
             Taxonomy (all) Sq,Scomp    -    [3]
     Absolute Magnitude (H)    19.09  mag    [5]
        Slope Parameter (G)     0.24  mag    [1]
                     Albedo    0.285    -    [8]
                   Diameter      375    m    [9]
    Color Index Information    0.362  R-I   [10]
                  Sightings  Radar R    -   [11]

Visit `Interfacing with the Pandas Package <https://docs.astropy.org/en/stable/table/pandas.html>`_ for further information.

##########################################
ESANEOCC Change Log
##########################################

==============================
Version 2.1
==============================

----------------------
Changes
----------------------

* Remove *parse* library dependency for Astroquery integration.

==============================
Version 2.0
==============================

----------------------
Changes
----------------------

* Configuration and file layout changes to start the Astroquery integration.

==============================
Version 1.4
==============================

----------------------
Changes
----------------------

* The type of the orbit is now obtained as attribute in tab *orbit_properties*.
* The format of the ephemerides data has been modified to adapt to the change of format of the ephemerides provided by `NEOCC portal <https://neo.ssa.esa.int/computer-access>`_ . This modification includes new parameters for the columns and also changes the precision of the Magnitude values up to two decimal digits.
* Tab *physical_properties* now contains all the values (if exist) for the different properties.
* There are two new lists implemented: Catalogue of NEAs (current date) and Catalogue of NEAs (middle arc).
* Parsing of tab *summary* is more robust.

----------------------
Bug Fixes
----------------------

* Fixed tab *observations* which failed to process the information of some asteroids.

==============================
Version 1.3.1
==============================

----------------------
Bug Fixes
----------------------
* Fixed bug where *risk_list* and *risk_list_special* were not displaying Torino Scale and Velocity.

==============================
Version 1.3
==============================

----------------------
Changes
----------------------

* `astropy <https://pypi.org/project/astropy/>`_ library has been added as required package.
* *neocc.py* module has been renamed to *core.py* in order to be consistent with Astroquery.
* *core.py* has been modified in order to be consistent with Astroquery (main class and static methods).
* Dates/time columns or data have been converted to datetime ISO format.
* Abbreviations contain now complete expressions (e.g., *close_appr_upcoming* to *close approaches_upcoming*)
* The documentation explains how to obtain JSON and Table format from data retrieved from the library.
* Time performance improvement in obtaining physical properties.

----------------------
Bug Fixes
----------------------

* Fixed two-points ephemerides generation fails
* Fixed physical properties generation for objects with Area-to-mass ratio and Yarkovsky parameter.
* Fixed orbit properties generation for objects with Area-to-mass ratio and Yarkovsky parameter.
