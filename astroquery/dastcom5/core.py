import re
import os
import urllib.request
import zipfile

from astropy.time import Time
from astropy.table import Table

from . import conf
from ..query import BaseQuery
from ..utils import async_to_sync

@async_to_sync
class Dastcom5Class(BaseQuery):
    """
    Class for querying NEOs orbit from DASTCOM5.
    """

    def __init__(self, spk_id=None, name=None):
        """
        Parameters:
        ----------
        api_key : str
            NASA OPEN APIs key (default: `DEMO_KEY`)
        """
        super(NeowsClass, self).__init__()
        self.spk_id = spk_id
        self.name = name
        self.local_path = conf.ASTROQUERY_LOCAL_PATH
        self.ast_path = conf.AST_DB_PATH
        self.com_path = conf.COM_DB_PATH
        self.com_dtype = conf.COM_DTYPE
        self.ast_dtype = conf.AST_DB_PATH


    def download_dastcom5(self):
        """Downloads DASTCOM5 database.

        Downloads and unzip DASTCOM5 file in default poliastro path (~/.poliastro).

        """

        dastcom5_dir = os.path.join(self.local_path, "dastcom5")
        dastcom5_zip_path = os.path.join(self.local_path, "dastcom5.zip")

        if os.path.isdir(dastcom5_dir):
            raise FileExistsError(
                "dastcom5 is already created in " + os.path.abspath(dastcom5_dir)
            )
        if not zipfile.is_zipfile(dastcom5_zip_path):
            if not os.path.isdir(self.local_path):
                os.makedirs(self.local_path)

            urllib.request.urlretrieve(
                FTP_DB_URL + "dastcom5.zip", dastcom5_zip_path, _show_download_progress
            )
        with zipfile.ZipFile(dastcom5_zip_path) as myzip:
            myzip.extractall(self.local_path)


    def asteroid_db():
        """Return complete DASTCOM5 asteroid database.

        Returns
        -------
        database : numpy.ndarray
            Database with custom dtype.

        """
        with open(AST_DB_PATH, "rb") as f:
            f.seek(835, os.SEEK_SET)
            data = np.fromfile(f, dtype=AST_DTYPE)
        return data



    def comet_db():
        """Return complete DASTCOM5 comet database.

        Returns
        -------
        database : numpy.ndarray
            Database with custom dtype.

        """
        with open(COM_DB_PATH, "rb") as f:
            f.seek(976, os.SEEK_SET)
            data = np.fromfile(f, dtype=COM_DTYPE)
        return data


    def _spk_id_from_name(self, name, cache=True):
        payload = {
            "sstr": name,
            "orb": "0",
            "log": "0",
            "old": "0",
            "cov": "0",
            "cad": "0",
        }
        SBDB_URL = conf.sbdb_server
        response = self._request(
            "GET", SBDB_URL, params=payload, timeout=self.TIMEOUT, cache=cahe)

        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        # page_identifier is used to check what type of response page we are working with.
        page_identifier = soup.find(attrs={"name": "top"})

        # If there is a 'table' sibling, the object was found.
        if page_identifier.find_next_sibling("table") is not None:
            data = page_identifier.find_next_sibling(
                "table").table.find_all("td")

            complete_string = ""
            for string in data[1].stripped_strings:
                complete_string += string + " "
            match = re.compile(r"Classification: ([\S\s]+) SPK-ID: (\d+)").match(
                complete_string
            )
            if match:
                self.spk_id = match.group(2)
                return match.group(2)

        # If there is a 'center' sibling, it is a page with a list of possible objects
        elif page_identifier.find_next_sibling("center") is not None:
            object_list = page_identifier.find_next_sibling("center").table.find_all(
                "td"
            )
            bodies = ""
            obj_num = min(len(object_list), 3)
            for body in object_list[:obj_num]:
                bodies += body.string + "\n"
            raise ValueError(
                str(len(object_list)) + " different bodies found:\n" + bodies
            )

        # If everything else failed
        raise ValueError("Object could not be found. You can visit: " +
                         SBDB_URL + "?sstr=" + name + " for more information.")

    def from_spk_id(self, spk_id, cache=True):
        """Return :py:class:`~astropy.table.Table` given a SPK-ID.

        Retrieve info from NASA NeoWS API, and therefore
        it only works with NEAs (Near Earth Asteroids).

        Parameters
        ----------
        spk_id : str
            SPK-ID number, which is given to each body by JPL.

        Returns
        -------
        Table : ~astropy.table.Table
            NEA orbit parameters.

        """
        payload = {"api_key": self.api_key or DEFAULT_API_KEY}

        NEOWS_URL = conf.neows_server
        response = self._request(
            "GET", NEOWS_URL + spk_id, params=payload, timeout=self.TIMEOUT, cache=cache
        )
        response.raise_for_status()

        orbital_data = response.json()["orbital_data"]
        self.name = response.json()["name"]
        abs_magnitude = response.json()["absolute_magnitude_h"]
        column1 = ["name", "absolute_magnitude_h"]
        column2 = [self.name, abs_magnitude]
        column1.extend(orbital_data.keys())
        column2.extend(orbital_data.values())
        data = Table([column1, column2], names=("Parameters", "Values"))
        self.epoch = Time(
            float(orbital_data["epoch_osculation"]), format="jd", scale="tdb"
        )

        return data

    def from_name(self, name, cache=True):
        if not self.spk_id:
            self._spk_id_from_name(name=name, cache=cache)
        return self.from_spk_id(spk_id=self.spk_id, cache=cache)


Neows = NeowsClass()
