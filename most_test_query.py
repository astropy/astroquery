URL = "https://irsa.ipac.caltech.edu/applications/MOST/"

import re
from bs4 import BeautifulSoup

from io import BytesIO
from astropy.table import Table, Column

import astroquery as aq
from astroquery import log
from astroquery.exceptions import LoginError, RemoteServiceError, NoResultsWarning
from astroquery.utils import schema, system_tools
from astroquery.query import QueryWithLogin, suspend_cache
#from . import conf


base_url = "https://irsa.ipac.caltech.edu/cgi-bin/MOST/nph-most?"
name_query_url = ("catalog=$CATALOG"
                  "&input_type=name_input"
                  "&obj_name=$OBJ_NAME"
                  "&obs_begin=$OBS_BEGIN"
                  "&obs_end=$OBS_END"
                  "&output_mode=$OUT_MODE")

aster_orbital_elem_url = ("catalog=$CATALOG"
                          "&input_type=name_input"
                          "&obs_begin=$OBS_BEGIN"
                          "&obs_end=$OBS_END"
                          "&obj_type=Asteroid"
                          "&input_type=manual_input"
                          "&body_designation=$BODY_DESIGNATIOn"
                          "&epoch=$EPOCH"
                          "&semimajor_axis=$SEMIMAJOR_AXIS"
                          "&eccentricity=$ECCENTRICITY"
                          "&inclination=$INCLINATION"
                          "&arg_perihelion=$ARG_PERIHELION"
                          "&ascend_node=$ASCEND_NODE"
                          "&mean_anomaly=$MEAN_ANOMALY"
                          "&output_mode=$OUT_MODE")

comet_orbital_elem_url = ("catalog=$CATALOG"
                          "&input_type=name_input"
                          "&obs_begin=$OBS_BEGIN"
                          "&obs_end=$OBS_END"
                          "&obj_type=Comet"
                          "&input_type=manual_input"
                          "&body_designation=$BODY_DESIGNATION"
                          "&epoch=$EPOCH"
                          "&perih_dist=$PERIH_DIST"
                          "&eccentricity=$ECCENTRICITY"
                          "&inclination=$INCLINATION"
                          "&arg_perihelion=$ARG_PERIHELION"
                          "&ascend_node=$ASCEND_NODE"
                          "&perih_time=$PERIH_TIME"
                          "&output_mode=$OUT_MODE")

mpc_aster = ("&obj_type=Asteroid"
             "&input_type=mpc_input"
             "&mpc_data=$MPC_DATA"
             "&output_mode=$OUT_MODE")

mpc_comet = ("&obj_type=Comet"
             "&input_type=mpc_input"
             "&mpc_data=$MPC_DATA"
             "&output_mode=Brief")


class BriefMOSTQuery(aq.query.BaseQuery):
    URL =  "https://irsa.ipac.caltech.edu/cgi-bin/MOST/nph-most?"
    def __init__(self):
        super().__init__()

    def _validate_params(self, params, input_type):
        # catalog is always required
        if not params.get("catalog", False):
            raise ValueError("Which catalog is being queried is always required.")

        # do not join this if, input_type validity is being checked too
        if input_type == "name_input":
            if not params.get("obj_name", False):
                raise ValueError("When input type is 'name_input' key 'obj_name' is required. "
                                 "Specify different 'input_type' or 'obj_name'.")
        elif input_type == "manual_input":
            obj_type = params.get("obj_type", False)
            if not obj_type:
                raise ValueError("When input_type is 'manual_input', 'obj_type' is required.")

            # MOST will always require at least the distance and eccentricity
            # distance param is named differently in cases of asteroids and comets
            if not params.get("eccentricity", False):
                raise ValueError("When input_type is 'manual_input', 'eccentricity' is required.")

            if obj_type == "Asteroid":
                if not params.get("semimajor_axis", False):
                    raise ValueError("When obj_type is 'Asteroid', 'semimajor_axis' is required.")
            elif obj_type == "Comet":
                if not params.get("perih_dist", False):
                    raise ValueError("When obj_type is 'Comet', 'perih_dist' is required.")
        elif input_type == "mpc_input":
            # MPC seems to work just fine without specifying Comet or Asteroid?
            if not params.get("mpc_data", False):
                raise ValueError("When input type is 'mpc_input', key 'mpc_data' is required.")
        else:
            raise ValueError("Unrecognized input_type. Expected 'name_input', "
                             f"manual_input or 'mpc_input'. Got {input_type} instead.")

    def _fill_default_params(self, params, input_type):
        #input_type could have been read from the dict, or defaulted to name
        # input in _create_url. We set it explicitly again, just in case
        params["input_type"] = input_type

        # currently brief mode is the only supported mode because otherwise
        # HTML needs parsing
        params["output_mode"] = "Brief"

        # this key is also required when in manual_input, but apparently it
        # can be whatever value
        if input_type == 'manual_input':
            if not params.get("body_designation", False):
                params["body_designation"] = "Test"+params["obj_type"]

        return params

    def _create_url_fragments(self, query_params):
        # we default to IRSA name query if nothing else is specified
        intype = query_params.get("input_type", False)
        input_type = intype if intype else "name_input"

        self._validate_params(query_params, input_type)
        query_params = self._fill_default_params(query_params, input_type)

        return "&".join((f"{k}={v}" for k, v in query_params.items()))

    def get_url(self, query_params):
        target = self._create_url_fragments(query_params)
        return self.URL + target

    def query(self, **query_params):
        response = self._request("GET", self.get_url(query_params))
        return Table.read(response.text, format="ipac")


class InterfaceMOSTQuery(aq.query.BaseQuery):
    def __init__(self):
        super().__init__()

    def _validate_params(self, params, input_type):
        # catalog is always required
        if not params.get("catalog", False):
            raise ValueError("Which catalog is being queried is always required.")

        # do not join this if, input_type validity is being checked too
        if input_type == "name_input":
            if not params.get("obj_name", False):
                raise ValueError("When input type is 'name_input' key 'obj_name' is required. "
                                 "Specify different 'input_type' or 'obj_name'.")
        elif input_type == "manual_input":
            obj_type = params.get("obj_type", False)
            if not obj_type:
                raise ValueError("When input_type is 'manual_input', 'obj_type' is required.")

            # MOST will always require at least the distance and eccentricity
            # distance param is named differently in cases of asteroids and comets
            if not params.get("eccentricity", False):
                raise ValueError("When input_type is 'manual_input', 'eccentricity' is required.")

            if obj_type == "Asteroid":
                if not params.get("semimajor_axis", False):
                    raise ValueError("When obj_type is 'Asteroid', 'semimajor_axis' is required.")
            elif obj_type == "Comet":
                if not params.get("perih_dist", False):
                    raise ValueError("When obj_type is 'Comet', 'perih_dist' is required.")
        elif input_type == "mpc_input":
            if not params.get("mpc_data", False):
                raise ValueError("When input type is 'mpc_input', key 'mpc_data' is required.")
        else:
            raise ValueError("Unrecognized input_type. Expected 'name_input', "
                             f"manual_input or 'mpc_input'. Got {input_type} instead.")

    def _fill_default_params(self, params, input_type):
        #input_type could have been read from the dict, or defaulted to name
        # input in _create_url. We set it explicitly again, just in case
        params["input_type"] = input_type

        # currently brief mode is the only supported mode because otherwise
        # HTML needs parsing
        params["output_mode"] = "Brief"

        # this key is also required when in manual_input, but apparently it
        # can be whatever value
        if input_type == 'manual_input':
            if not params.get("body_designation", False):
                params["body_designation"] = "Test"+params["obj_type"]

        return params

    def _create_url_fragments(self, query_params):
        # we default to IRSA name query if nothing else is specified
        intype = query_params.get("input_type", False)
        input_type = intype if intype else "name_input"

        self._validate_params(query_params, input_type)
        query_params = self._fill_default_params(query_params, input_type)

        return "&".join((f"{k}={v}" for k, v in query_params.items()))

    def get_url(self, query_params):
        target = self._create_url_fragments(query_params)
        return base_url + target

    def query(self, **query_params):
        response = self._request("GET", self.get_url(query_params))
        return Table.read(response.text, format="ipac")


# import bs4
# import astropy.io as aio
# from astropy.table import Table
#
# with open("....") as f:
#     html = bs4.BeautifulSoup(f)
#
# for the first table: (ephemerides)
# allpres = html.find_all("pre")
# lines = allpres.split("\n")
# info = lines[:13]
# tblheader = lines[13]
# columns = tblheader.replace("(J2000)", "")
# columns = columns.split()
# txttable = lines[14:-3]
# Table.read(table, format="ascii", names=columns)
# 14+1, 15+24=39, 39+11=50, 50+11=61, 61+11=72, 72+11=83, 83+11=94, 94+7=101, 101+5=106
# table = aio.ascii.read(txttable, format="fixed_width_no_header", col_ends=(15, 39, 51, 64, 78, 90, 103, 118, 129, 139, 145))
# table.rename(list(table.columns), columns)

# second table: search results
# Table.read(allpres[3].text, format="ipac")

# third table: images
# alltables = html.find_all("table")
# imgtable = alltables[-1]
# super annoying because the table has 2 row header and it breaks HTML class in Astropy
# so we cut the first two rows out of the table, rebuild the table and then parse it via Astropy
# rows = imgtable.find_all("tr")
# "<table><tbody>" + "".join([i.renderContents().decode() for i in rows[2:]]) + "</tbody></table>"
# this table is duplicate of the second table?

# quick way to get images
# allimgs = html.find_all("img", alt="FITS")
# alllinks = [i.parent["href"] for i in allimgs]

# regions = html.find_all("a", text="region")

mostq = BriefMOSTQuery()
# mostq.query() --> ValueError
# mostq.query(catalog="wise_allsky_4band") # --> ValueError
# mostq.query(catalog="wise_allsky_4band", obj_name="Victoria") # --> catalog=wise_allsky_4band&obj_name=Victoria&input_type=name_input&output_mode=Brief
# mostq.query(catalog="wise_allsky_4band", input_type="name_input", obj_name="Victoria") # --> catalog=wise_allsky_4band&input_type=name_input&obj_name=Victoria&output_mode=Brief
# mostq.query(catalog="wise_allsky_4band", output_mode="Brief", input_type="name_input", obj_name="Victoria") # --> catalog=wise_allsky_4band&input_type=name_input&obj_name=Victoria&output_mode=Brief
# mostq.query(catalog="wise_allsky_4band", output_mode="Brief", input_type="manual_input", obj_type="Asteroid", perih_dist=1.5, eccentricity=0.5) # --> ValueError
# mostq.query(catalog="wise_allsky_4band", output_mode="Brief", input_type="manual_input", obj_type="Asteroid", semimajor_axis=2.68, eccentricity=0.33) # --> catalog=wise_allsky_4band&output_mode=Brief&input_type=manual_input&obj_type=Asteroid&semimajor_axis=2.68&eccentricity=0.33&body_designation=TestAsteroid
# mostq.query(catalog="wise_allsky_4band", output_mode="Brief", input_type="manual_input", obj_type="Comet", semimajor_axis=2.68, eccentricity=0.33) # --> ValueError
# mostq.query(catalog="wise_allsky_4band", output_mode="Brief", input_type="manual_input", obj_type="Comet", perih_dist=2.68, eccentricity=0.33) # --> catalog=wise_allsky_4band&output_mode=Brief&input_type=manual_input&obj_type=Comet&perih_dist=2.68&eccentricity=0.33&body_designation=TestComet
# mostq.query(catalog="wise_allsky_4band", output_mode="Brief", input_type="mpc_input") # --> ValueError
#mostq.query(catalog="wise_allsky_4band", output_mode="Brief", input_type="mpc_input", mpc_data="00324+6.82+0.09+K103I+64.7389713+43.9047086+ 327.9898280+11.1080776+0.33709263+0.2240550+2.684723515+0+MPO344295+2289+63+ 1892-2015+0.50+M-v+38h+MPCLINUX+0000+(324)+Bamberga+20150614") # --> ValueError

# mostq.query(catalog="wise_allsky_4band", input_type="name_input") # --> catalog=wise_allsky_4band&input_type=name_input


# catalog
# obs_begin
# obs_end
# ephem_step
# output_mode
# fits_region_files
# input_type --> obj_name, nafid_input, mpc_input, manual_input
# obj_name, obj_nafid, (obj_type[Asteroid, Comet], mpc_data), (body_designation, epoch, eccentricity, inclination, arg_perihelion, ascend_node, semimajor_axis, mean_anomaly, perih_dist, perih_time)
# \


class InterfaceMOSTQuery(aq.query.BaseQuery):
    URL = 'https://irsa.ipac.caltech.edu/cgi-bin/MOST/nph-most'

    _default_qparams = {
        "catalog": "wise_merge",
        "input_type": "name_input",
        "output_mode": "Full",
        "obs_begin": None,
        "obs_end": None,
        "ephem_step": 0.25,
        "output_mode": "Full",
        "fits_region_files": False,
        "obj_name": None,
        "obj_nafid": None,
        "obj_type": None,
        "mpc_data": None,
        "body_designation": None,
        "epoch": None,
        "eccentricity": None,
        "inclination": None,
        "arg_perihelion": None,
        "ascend_node": None,
        "semimajor_axis": None,
        "mean_anomaly": None,
        "perih_dist": None,
        "perih_time": None
    }

    def __init__(self):
        super().__init__()

    def _validate_name_input_type(self, params):
        if not params.get("obj_name", False):
            raise ValueError("When input type is 'name_input' key 'obj_name' is required.")

    def _validate_nafid_input_type(self, params):
        if not params.get("obj_nafid", False):
            raise ValueError("When input type is 'nafid_input' key 'obj_nafid' is required.")

    def _validate_mpc_input_type(self, params):
        obj_type = params.get("obj_type", False)
        if not obj_type:
            raise ValueError("When input type is 'mpc_input' key 'obj_type' is required.")
        if obj_type not in ("Asteroid", "Comet"):
            raise ValueError("Object type is case sensitive and must be one of: `Asteroid` or `Comet`")

        if not params.get("mpc_data", False):
            raise ValueError("When input type is 'mpc_input' key 'mpc_data' is required.")

    def _validate_manual_input_type(self, params):
        obj_type = params.get("obj_type", False)
        if not obj_type:
            raise ValueError("When input type is 'mpc_input' key 'obj_type' is required.")
        if obj_type not in ("Asteroid", "Comet"):
            raise ValueError("Object type is case sensitive and must be one of: `Asteroid` or `Comet`")

        # MOST will always require at least the distance and eccentricity
        # distance param is named differently in cases of asteroids and comets
        if not params.get("eccentricity", False):
            raise ValueError("When input_type is 'manual_input', 'eccentricity' is required.")

        if obj_type == "Asteroid":
            if not params.get("semimajor_axis", False):
                raise ValueError("When obj_type is 'Asteroid', 'semimajor_axis' is required.")
        elif obj_type == "Comet":
            if not params.get("perih_dist", False):
                raise ValueError("When obj_type is 'Comet', 'perih_dist' is required.")

        # This seemingly can be whatever
        if not params.get("body_designation", False):
                params["body_designation"] = "Test"+params["obj_type"]

    def _validate_input(self, params):
        if not params.get("catalog", False):
            raise ValueError("Which catalog is being queried is always required.")

        input_type = params.get("input_type", False)
        if not input_type:
            raise ValueError("Input type is always required.")

        if input_type == "name_input":
            self._validate_name_input_type(params)
        elif input_type == "nafid_input":
            self._validate_nafid_input_type(params)
        elif input_type == "mpc_input":
            self._validate_mpc_input_type(params)
        elif input_type == "manual_input":
            self._validate_manual_input_type(params)
        else:
            raise ValueError(
                "Unrecognized `input_type`. Expected `name_input`, `nafid_input` "
                f"`mpc_input` or `manual_input`, got {input_type} instead."
            )

        # We're not supporting parsing anything else except full output atm
        output_mode = params.get("output_mode", False)
        if not output_mode or output_mode != "Full":
            raise ValueError("Only `Full` output mode is currently supported.")

    def _parse_ephemerides_tag(self, tag):
        lines = tag.text.split("\n")

        # Info basically contains the query values
        info = lines[:13]

        # header contains the columns, alongside their units in parenthesis, we
        # don't want to have to spell those out when referencing the column in
        # code - so we remove the units from column names
        header = lines[13]
        columns = header.replace("(J2000)", "")
        columns = columns.split()

        # These are the actual retrieved values for columns, the end couple of
        # lines of the tag are N objects retrieved, time taken etc.
        table = lines[14:-3]
        table = aio.ascii.read(
            txttable,
            format="fixed_width_no_header",
            col_ends=(15, 39, 51, 64, 78, 90, 103, 118, 129, 139, 145)
        )
        table.rename(list(table.columns), columns)

        return table

    def _parse_full_response(self, response):
        html = BeautifulSoup(response.content)

        # parse ephemerides table from html
        all_pre_tags = html.find_all("pre")
        ephem_tag = all_pre_tags[1]
        ephemerides = self._parse_ephemerides_tag(ephem_tag)

        # parse the search results, second table
        search_results_tag = all_pre_tags[3]
        search_results = Table.read(search_results_tag.text, format="ipac")

        # parse the links to images and regions, third table
        # we don't  parse the full table because values already exist in 2nd
        # table
        fits_tags = html.find_all("img", alt="FITS")
        fits_hrefs = [i.parent["href"] for i in fits_tags]
        fits = Column(name="fits_download", data=fits_hrefs)

        region_tags = html.find_all("a", text="region")
        region_hrefs = [i["href"] for i in region_tags]
        regions = Column(name="region_download", data=region_hrefs)

        search_results.add_columns((fits, regions))

        return {"ephemerides": ephemerides, "search_results": search_results}

    def _parse_full_regular_response(self, response, withTarballs=False):
        retdict = {}
        html = BeautifulSoup(response.content)
        download_tags = html.find_all("a", text=re.compile(".*Download.*"))

        # this is "Download Results Table (above)"
        results_response = self._request("GET", download_tags[0]["href"])
        retdict["results"] = Table.read(results_response.text, format="ipac")

        # this is "Download Image Metadata with Matched Object position Table"
        imgmet_response = self._request("GET", download_tags[1]["href"])
        retdict["metadata"] = Table.read(imgmet_response.text, format="ipac")

        # this is "Download DS9 Region File with the Orbital Path", it's a link
        # to a DS9 region file
        # regions_response = self._request("GET", download_tags[2]["href"])
        retdict["region"] = download_tags[2]["href"]

        if withTarballs:
            retdict["fits_tarball"] = download_tags[-1]["href"]
            retdict["regions_tarball"] = download_tags[-2]["href"]

        return retdict

    def query(self, **query_params):
        qparams = self._default_qparams.copy()
        qparams.update(query_params)
        self._validate_input(qparams)
        response = self._request("POST", self.URL, data=qparams)

        if qparams["output_mode"] in ("Brief", "Gator"):
            return Table.read(response.text, format="ipac")
        elif qparams["output_mode"] == "VOTable":
            return aio.votable.parse(response.content)
        else:
            return self._parse_full_regular_response(response, qparams["fits_region_files"])



most = InterfaceMOSTQuery()
res = most.query(obj_name="Victoria", obs_begin="2014-05-01", obs_end="2014-05-30")

breakpoint()

a = 1
a + 1
