from . import conf
from astroquery.query import BaseQuery


__all__ = ['NEODyS', 'NEODySClass']


class NEODySClass(BaseQuery):

    NEODYS_URL = conf.server
    TIMEOUT = conf.timeout

    def query_object(self, object_id, *, orbital_element_type="eq", epoch_near_present=0):
        """
        Parameters
        ----------
        object_id : str
            Name of objects to be searched in NEODyS website

        orbital_element_type : str
            Sets coordinate system for results.
            eq - Equinoctial
            ke - Keplerian
            Defaults to Equinoctial which is given in higher
            precision.

        epoch_near_present : bool
            Sets the epoch to near present day. Otherwise
            defaults to near middle of the arc.

        Returns
        -------

        Returns a dictionary with the following entries:

        KEP : float array
            The state vector in Keplerian elements.
            Units in au and deg.

        EQU : float array
            The state vector in Equinoctial elements.

        COV : float array
            The covariance matrix.

        COR : float array
            The correlation matrix for Keplerian.

        MJD : str array
            The Mean Julian date, and the time scale
            used.

        MAG : float array
            The absolute magnitude (H) and slope
            parameter (G)

        Raises
        ------
        ValueError
            If input parameters are invalid.

        RuntimeError
            If connection to website fails.

        """

        COV = []
        COR = []

        if orbital_element_type != 'ke' and orbital_element_type != 'eq':
            raise ValueError("OrbitElementType must be ke or eq")

        object_url = f'{self.NEODYS_URL}/{object_id}.{orbital_element_type}{epoch_near_present}'

        response = self._request('GET', object_url, timeout=self.TIMEOUT)
        response.raise_for_status()

        ascii_text = (response.text).split('\n')

        results = {}

        for line in ascii_text:
            if 'KEP' in line:
                results["Keplerian State Vector"] = [float(x) for x in line.split()[1:]]
            if 'EQU' in line:
                results["Equinoctial State Vector"] = [float(x) for x in line.split()[1:]]
            if 'MJD' in line:
                results["Mean Julian Date"] = line.split()[1:]
            if 'MAG' in line:
                results["Magnitude"] = [float(x) for x in line.split()[1:]]
            if 'COV' in line:
                COV.extend([float(x) for x in line.split()[1:]])
            if 'COR' in line:
                COR.extend([float(x) for x in line.split()[1:]])
        results["Covariance Matrix"] = COV
        results["Keplerian Correlation Matrix"] = COR
        results["URL"] = object_url

        return results


NEODyS = NEODySClass()
