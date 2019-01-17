import re
import os
import urllib.request
import zipfile
import numpy as np

from astropy.time import Time
from astropy.table import Table, vstack
import astropy.units as u

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
        super(Dastcom5Class, self).__init__()
        self.spk_id = spk_id
        self.name = name
        self.local_path = conf.ASTROQUERY_LOCAL_PATH
        self.dbs_path = conf.DBS_LOCAL_PATH
        self.ast_path = conf.AST_DB_PATH
        self.com_path = conf.COM_DB_PATH
        self.com_dtype = conf.COM_DTYPE
        self.ast_dtype = conf.AST_DTYPE
        self.ftp_url = conf.FTP_DB_URL

    def download_dastcom5(self):
        """Downloads DASTCOM5 database.

        Downloads and unzip DASTCOM5 file in default astroquery path (~/.astroquery).

        """

        dastcom5_dir = os.path.join(self.local_path, "dastcom5")
        dastcom5_zip_path = os.path.join(self.local_path, "dastcom5.zip")

        if os.path.isdir(dastcom5_dir):
            raise FileExistsError(
                "dastcom5 is already created in " +
                os.path.abspath(dastcom5_dir)
            )
        if not zipfile.is_zipfile(dastcom5_zip_path):
            if not os.path.isdir(self.local_path):
                os.makedirs(self.local_path)

            urllib.request.urlretrieve(
                self.ftp_url + "dastcom5.zip", dastcom5_zip_path, self._show_download_progress
            )
        with zipfile.ZipFile(dastcom5_zip_path) as myzip:
            myzip.extractall(self.local_path)

    def _show_download_progress(self, transferred, block, totalsize):
        trans_mb = transferred * block / (1024 * 1024)
        total_mb = totalsize / (1024 * 1024)
        print("%.2f MB / %.2f MB" % (trans_mb, total_mb), end="\r", flush=True)

    def asteroid_db(self):
        """Return complete DASTCOM5 asteroid database.

        Returns
        -------
        database : numpy.ndarray
            Database with custom dtype.

        """
        with open(self.ast_path, "rb") as f:
            f.seek(835, os.SEEK_SET)
            data = np.fromfile(f, dtype=self.ast_dtype)
        return data

    def comet_db(self):
        """Return complete DASTCOM5 comet database.

        Returns
        -------
        database : numpy.ndarray
            Database with custom dtype.

        """
        with open(self.com_path, "rb") as f:
            f.seek(976, os.SEEK_SET)
            data = np.fromfile(f, dtype=self.com_dtype)
        return data

    def read_headers(self):
        """Read `DASTCOM5` headers and return asteroid and comet headers.

        Headers are two numpy arrays with custom dtype.

        Returns
        -------
        ast_header, com_header : tuple (numpy.ndarray)
            DASTCOM5 headers.

        """

        ast_path = os.path.join(self.dbs_path, "dast5_le.dat")
        ast_dtype = np.dtype(
            [
                ("IBIAS1", np.int32),
                ("BEGINP1", "|S8"),
                ("BEGINP2", "|S8"),
                ("BEGINP3", "|S8"),
                ("ENDPT1", "|S8"),
                ("ENDPT2", "|S8"),
                ("ENDPT3", "|S8"),
                ("CALDATE", "|S19"),
                ("JDDATE", np.float64),
                ("FTYP", "|S1"),
                ("BYTE2A", np.int16),
                ("IBIAS0", np.int32),
            ]
        )

        with open(ast_path, "rb") as f:
            ast_header = np.fromfile(f, dtype=ast_dtype, count=1)

        com_path = os.path.join(self.dbs_path, "dcom5_le.dat")
        com_dtype = np.dtype(
            [
                ("IBIAS2", np.int32),
                ("BEGINP1", "|S8"),
                ("BEGINP2", "|S8"),
                ("BEGINP3", "|S8"),
                ("ENDPT1", "|S8"),
                ("ENDPT2", "|S8"),
                ("ENDPT3", "|S8"),
                ("CALDATE", "|S19"),
                ("JDDATE", np.float64),
                ("FTYP", "|S1"),
                ("BYTE2C", np.int16),
            ]
        )

        with open(com_path, "rb") as f:
            com_header = np.fromfile(f, dtype=com_dtype, count=1)

        return ast_header, com_header

    def entire_db(self):
        """Return complete DASTCOM5 database.

        Merge asteroid and comet databases, only with fields
        related to orbital data, discarding the rest.

        Returns
        -------
        database : numpy.ndarray
            Database with custom dtype.

        """
        ast_database = self.asteroid_db()
        com_database = self.comet_db()

        ast_database = pd.DataFrame(
            ast_database[
                list(ast_database.dtype.names[:17]) +
                list(ast_database.dtype.names[-4:-3]) +
                list(ast_database.dtype.names[-2:])
            ]
        )
        ast_database.rename(
            columns={"ASTNAM": "NAME", "NO": "NUMBER", "CALEPO": "CALEPOCH"}, inplace=True
        )
        com_database = pd.DataFrame(
            com_database[
                list(com_database.dtype.names[:17]) +
                list(com_database.dtype.names[-4:-3]) +
                list(com_database.dtype.names[-2:])
            ]
        )
        com_database.rename(
            columns={"COMNAM": "NAME", "NO": "NUMBER", "CALEPO": "CALEPOCH"}, inplace=True
        )
        df = ast_database.append(com_database, ignore_index=True)
        df[["NAME", "DESIG", "IREF"]] = df[["NAME", "DESIG", "IREF"]].apply(
            lambda x: x.str.strip().str.decode("utf-8")
        )
        return df

    def read_record(self, record):
        """Read `DASTCOM5` record and return body data.

        Body data consists of numpy array with custom dtype.

        Parameters
        ----------
        record : int
            Body record.

        Returns
        -------
        body_data : numpy.ndarray
            Body information.

        """
        ast_header, com_header = self.read_headers()
        ast_path = os.path.join(self.dbs_path, "dast5_le.dat")
        com_path = os.path.join(self.dbs_path, "dcom5_le.dat")
        # ENDPT1 indicates end of numbered asteroids records
        if record <= int(ast_header["ENDPT2"][0].item()):
            # ENDPT2 indicates end of unnumbered asteroids records
            if record <= int(ast_header["ENDPT1"][0].item()):
                # phis_rec = record_size * (record_number - IBIAS - 1 (header record))
                phis_rec = 835 * (record - ast_header["IBIAS0"][0].item() - 1)
            else:
                phis_rec = 835 * (record - ast_header["IBIAS1"][0].item() - 1)

            with open(ast_path, "rb") as f:
                f.seek(phis_rec, os.SEEK_SET)
                body_data = np.fromfile(f, dtype=self.ast_dtype, count=1)
        else:
            phis_rec = 976 * (record - com_header["IBIAS2"][0].item() - 1)
            with open(com_path, "rb") as f:
                f.seek(phis_rec, os.SEEK_SET)
                body_data = np.fromfile(f, dtype=self.com_dtype, count=1)
        return body_data

    def orbit_from_name(self, name):
        """Return :py:class:`~astropy.table.Table` given a name.

        Retrieve info from JPL DASTCOM5 database.

        Parameters
        ----------
        name : str
            NEO name.

        Returns
        -------
        Table : ~astropy.table.Table
            Near Earth Asteroid/Comet orbit parameters, all stacked.

        """
        records = self.record_from_name(name)
        table = self.orbit_from_record(records[0])
        for i in range(1, len(records)):
            table = vstack([table, self.orbit_from_record(records[i])[1]])
        return table

    def orbit_from_record(self, record):
        """Return :py:class:`~astropy.table.Table` given a record.

            Retrieve info from JPL DASTCOM5 database.

            Parameters
            ----------
            record : int
                Object record.

            Returns
            -------
            Table : ~astropy.table.Table
                Near Earth Asteroid/Comet orbit parameters.

            """
        body_data = self.read_record(record)
        a = body_data["A"].item()
        ecc = body_data["EC"].item()
        inc = body_data["IN"].item()
        raan = body_data["OM"].item()
        argp = body_data["W"].item()
        m = body_data["MA"].item()
        epoch = Time(body_data["EPOCH"].item(), format="jd", scale="tdb")
        column2 = (record, a, ecc, inc, raan, argp, m, epoch)
        column1 = ("record", "a", "ecc", "inc", "raan", "argp", "m", "EPOCH")
        data = Table(rows=[column1, column2])

        return data

    def record_from_name(self, name):
        """Search `dastcom.idx` and return logical records that match a given string.

        Body name, SPK-ID, or alternative designations can be used.

        Parameters
        ----------
        name : str
            Body name.

        Returns
        -------
        records : list (int)
            DASTCOM5 database logical records matching str.

        """
        records = []
        lines = self.string_record_from_name(name)
        for line in lines:
            records.append(int(line[:6].lstrip()))
        return records

    def string_record_from_name(self, name):
        """Search `dastcom.idx` and return body full record.

        Search DASTCOM5 index and return body records that match string,
        containing logical record, name, alternative designations, SPK-ID, etc.

        Parameters
        ----------
        name : str
            Body name.

        Returns
        -------
        lines: list(str)
            Body records
        """

        idx_path = os.path.join(self.dbs_path, "dastcom.idx")
        lines = []
        with open(idx_path, "r") as inF:
            for line in inF:
                if re.search(r"\b" + name.casefold() + r"\b", line.casefold()):
                    lines.append(line)
        return lines


Dastcom5 = Dastcom5Class()
