import re

from bs4 import BeautifulSoup

from astropy.time import Time
from astropy.table import Table

from . import conf
from ..query import BaseQuery
from ..utils import async_to_sync

DEFAULT_API_KEY = "DEMO_KEY"


@async_to_sync
class NeowsClass(BaseQuery):
    """
    Class for querying NEOs orbit from NEOWS and JPL SBDB.
    """

    def __init__(self, api_key=None, spk_id=None, name=None):
        """
        Parameters:
        ----------
        api_key : str
            NASA OPEN APIs key (default: `DEMO_KEY`)
        """
        super(NeowsClass, self).__init__()
        self.spk_id = spk_id
        self.name = name
        self.TIMEOUT = conf.timeout
        self.api_key = api_key

    def _spk_id_from_name(self, name):
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
            "GET", SBDB_URL, params=payload, timeout=self.TIMEOUT)

        # response = requests.get(SBDB_URL, params=payload)
        response.raise_for_status()
        # soup = BeautifulSoup(response.text, "html.parser")
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

    def from_spk_id(self, spk_id):
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
            "GET", NEOWS_URL + spk_id, params=payload, timeout=self.TIMEOUT
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

    def from_name(self, name):
        if not self.spk_id:
            self._spk_id_from_name(name=name)
        return self.from_spk_id(spk_id=self.spk_id)


Neows = NeowsClass()
