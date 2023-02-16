from astropy.table import Table
from astropy import units as u

from ..query import BaseQuery
from ..utils import async_to_sync, prepend_docstr_nosections
from . import conf
from .utils import parse_readme

__all__ = ['Hitran', 'HitranClass']


@async_to_sync
class HitranClass(BaseQuery):

    QUERY_URL = conf.query_url
    TIMEOUT = conf.timeout
    FORMATFILE = conf.formatfile
    ISO_INDEX = {'id': 0, 'iso_name': 1, 'abundance': 2, 'mass': 3,
                 'mol_name': 4}

# Copied from the hapi.py code (Academic Free License)
# http://hitran.org/static/hapi/hapi.py
# M I id iso_name abundance mass mol_name
    ISO = {
        (1, 1): [1, 'H2(16O)', 0.997317, 18.010565, 'H2O'],
        (1, 2): [2, 'H2(18O)', 0.00199983, 20.014811, 'H2O'],
        (1, 3): [3, 'H2(17O)', 0.000372, 19.01478, 'H2O'],
        (1, 4): [4, 'HD(16O)', 0.00031069, 19.01674, 'H2O'],
        (1, 5): [5, 'HD(18O)', 0.000000623, 21.020985, 'H2O'],
        (1, 6): [6, 'HD(17O)', 0.000000116, 20.020956, 'H2O'],
        (2, 1): [7, '(12C)(16O)2', 0.9842, 43.98983, 'CO2'],
        (2, 2): [8, '(13C)(16O)2', 0.01106, 44.993185, 'CO2'],
        (2, 3): [9, '(16O)(12C)(18O)', 0.0039471, 45.994076, 'CO2'],
        (2, 4): [10, '(16O)(12C)(17O)', 0.000734, 44.994045, 'CO2'],
        (2, 5): [11, '(16O)(13C)(18O)', 0.00004434, 46.997431, 'CO2'],
        (2, 6): [12, '(16O)(13C)(17O)', 0.00000825, 45.9974, 'CO2'],
        (2, 7): [13, '(12C)(18O)2', 0.0000039573, 47.998322, 'CO2'],
        (2, 8): [14, '(17O)(12C)(18O)', 0.00000147, 46.998291, 'CO2'],
        (2, 0): [15, '(13C)(18O)2', 0.000000044967, 49.001675, 'CO2'],
        (2, 11): [120, '(18O)(13C)(17O)', 0.00000001654, 48.00165, 'CO2'],
        (2, 9): [121, '(12C)(17O)2', 0.0000001368, 45.998262, 'CO2'],
        (3, 1): [16, '(16O)3', 0.992901, 47.984745, 'O3'],
        (3, 2): [17, '(16O)(16O)(18O)', 0.00398194, 49.988991, 'O3'],
        (3, 3): [18, '(16O)(18O)(16O)', 0.00199097, 49.988991, 'O3'],
        (3, 4): [19, '(16O)(16O)(17O)', 0.00074, 48.98896, 'O3'],
        (3, 5): [20, '(16O)(17O)(16O)', 0.00037, 48.98896, 'O3'],
        (4, 1): [21, '(14N)2(16O)', 0.990333, 44.001062, 'N2O'],
        (4, 2): [22, '(14N)(15N)(16O)', 0.0036409, 44.998096, 'N2O'],
        (4, 3): [23, '(15N)(14N)(16O)', 0.0036409, 44.998096, 'N2O'],
        (4, 4): [24, '(14N)2(18O)', 0.00198582, 46.005308, 'N2O'],
        (4, 5): [25, '(14N)2(17O)', 0.000369, 45.005278, 'N2O'],
        (5, 1): [26, '(12C)(16O)', 0.98654, 27.994915, 'CO'],
        (5, 2): [27, '(13C)(16O)', 0.01108, 28.99827, 'CO'],
        (5, 3): [28, '(12C)(18O)', 0.0019782, 29.999161, 'CO'],
        (5, 4): [29, '(12C)(17O)', 0.000368, 28.99913, 'CO'],
        (5, 5): [30, '(13C)(18O)', 0.00002222, 31.002516, 'CO'],
        (5, 6): [31, '(13C)(17O)', 0.00000413, 30.002485, 'CO'],
        (6, 1): [32, '(12C)H4', 0.98827, 16.0313, 'CH4'],
        (6, 2): [33, '(13C)H4', 0.0111, 17.034655, 'CH4'],
        (6, 3): [34, '(12C)H3D', 0.00061575, 17.037475, 'CH4'],
        (6, 4): [35, '(13C)H3D', 0.0000049203, 18.04083, 'CH4'],
        (7, 1): [36, '(16O)2', 0.995262, 31.98983, 'O2'],
        (7, 2): [37, '(16O)(18O)', 0.00399141, 33.994076, 'O2'],
        (7, 3): [38, '(16O)(17O)', 0.000742, 32.994045, 'O2'],
        (8, 1): [39, '(14N)(16O)', 0.993974, 29.997989, 'NO'],
        (8, 2): [40, '(15N)(16O)', 0.0036543, 30.995023, 'NO'],
        (8, 3): [41, '(14N)(18O)', 0.00199312, 32.002234, 'NO'],
        (9, 1): [42, '(32S)(16O)2', 0.94568, 63.961901, 'SO2'],
        (9, 2): [43, '(34S)(16O)2', 0.04195, 65.957695, 'SO2'],
        (10, 1): [44, '(14N)(16O)2', 0.991616, 45.992904, 'NO2'],
        (11, 1): [45, '(14N)H3', 0.9958715, 17.026549, 'NH3'],
        (11, 2): [46, '(15N)H3', 0.0036613, 18.023583, 'NH3'],
        (12, 1): [47, 'H(14N)(16O)3', 0.98911, 62.995644, 'HNO3'],
        (12, 2): [117, 'H(15N)(16O)3', 0.003636, 63.99268, 'HNO3'],
        (13, 1): [48, '(16O)H', 0.997473, 17.00274, 'OH'],
        (13, 2): [49, '(18O)H', 0.00200014, 19.006986, 'OH'],
        (13, 3): [50, '(16O)D', 0.00015537, 18.008915, 'OH'],
        (14, 1): [51, 'H(19F)', 0.99984425, 20.006229, 'HF'],
        (14, 2): [110, 'D(19F)', 0.000115, 21.0125049978, 'HF'],
        (15, 1): [52, 'H(35Cl)', 0.757587, 35.976678, 'HCl'],
        (15, 2): [53, 'H(37Cl)', 0.242257, 37.973729, 'HCl'],
        (15, 3): [107, 'D(35Cl)', 0.000118005, 36.9829544578, 'HCl'],
        (15, 4): [108, 'D(37Cl)', 0.000037735, 38.9800043678, 'HCl'],
        (16, 1): [54, 'H(79Br)', 0.50678, 79.92616, 'HBr'],
        (16, 2): [55, 'H(81Br)', 0.49306, 81.924115, 'HBr'],
        (16, 3): [111, 'D(79Br)', 0.0000582935, 80.9324388778, 'HBr'],
        (16, 4): [112, 'D(81Br)', 0.0000567065, 82.9303923778, 'HBr'],
        (17, 1): [56, 'H(127I)', 0.99984425, 127.912297, 'HI'],
        (17, 2): [113, 'D(127I)', 0.000115, 128.918574778, 'HI'],
        (18, 1): [57, '(35Cl)(16O)', 0.75591, 50.963768, 'ClO'],
        (18, 2): [58, '(37Cl)(16O)', 0.24172, 52.960819, 'ClO'],
        (19, 1): [59, '(16O)(12C)(32S)', 0.93739, 59.966986, 'OCS'],
        (19, 2): [60, '(16O)(12C)(34S)', 0.04158, 61.96278, 'OCS'],
        (19, 3): [61, '(16O)(13C)(32S)', 0.01053, 60.970341, 'OCS'],
        (19, 4): [62, '(16O)(12C)(33S)', 0.01053, 60.966371, 'OCS'],
        (19, 5): [63, '(18O)(12C)(32S)', 0.00188, 61.971231, 'OCS'],
        (20, 1): [64, 'H2(12C)(16O)', 0.98624, 30.010565, 'H2CO'],
        (20, 2): [65, 'H2(13C)(16O)', 0.01108, 31.01392, 'H2CO'],
        (20, 3): [66, 'H2(12C)(18O)', 0.0019776, 32.014811, 'H2CO'],
        (21, 1): [67, 'H(16O)(35Cl)', 0.75579, 51.971593, 'HOCl'],
        (21, 2): [68, 'H(16O)(37Cl)', 0.24168, 53.968644, 'HOCl'],
        (22, 1): [69, '(14N)2', 0.9926874, 28.006147, 'N2'],
        (22, 2): [118, '(14N)(15N)', 0.0072535, 29.997989, 'N2'],
        (23, 1): [70, 'H(12C)(14N)', 0.98511, 27.010899, 'HCN'],
        (23, 2): [71, 'H(13C)(14N)', 0.01107, 28.014254, 'HCN'],
        (23, 3): [72, 'H(12C)(15N)', 0.0036217, 28.007933, 'HCN'],
        (24, 1): [73, '(12C)H3(35Cl)', 0.74894, 49.992328, 'CH3Cl'],
        (24, 2): [74, '(12C)H3(37Cl)', 0.23949, 51.989379, 'CH3Cl'],
        (25, 1): [75, 'H2(16O)2', 0.994952, 34.00548, 'H2O2'],
        (26, 1): [76, '(12C)2H2', 0.9776, 26.01565, 'C2H2'],
        (26, 2): [77, '(12C)(13C)H2', 0.02197, 27.019005, 'C2H2'],
        (26, 3): [105, '(12C)2HD', 0.00030455, 27.021825, 'C2H2'],
        (27, 1): [78, '(12C)2H6', 0.97699, 30.04695, 'C2H6'],
        (27, 2): [106, '(12C)H3(13C)H3', 0.021952611, 31.050305, 'C2H6'],
        (28, 1): [79, '(31P)H3', 0.99953283, 33.997238, 'PH3'],
        (29, 1): [80, '(12C)(16O)(19F)2', 0.98654, 65.991722, 'COF2'],
        (29, 2): [119, '(13C)(16O)(19F)2', 0.0110834, 66.995083, 'COF2'],
        (31, 1): [81, 'H2(32S)', 0.94988, 33.987721, 'H2S'],
        (31, 2): [82, 'H2(34S)', 0.04214, 35.983515, 'H2S'],
        (31, 3): [83, 'H2(33S)', 0.007498, 34.987105, 'H2S'],
        (32, 1): [84, 'H(12C)(16O)(16O)H', 0.983898, 46.00548, 'HCOOH'],
        (33, 1): [85, 'H(16O)2', 0.995107, 32.997655, 'HO2'],
        (34, 1): [86, '(16O)', 0.997628, 15.994915, 'O'],
        (36, 1): [87, '(14N)(16O)+', 0.993974, 29.997989, 'NOp'],
        (37, 1): [88, 'H(16O)(79Br)', 0.5056, 95.921076, 'HOBr'],
        (37, 2): [89, 'H(16O)(81Br)', 0.4919, 97.919027, 'HOBr'],
        (38, 1): [90, '(12C)2H4', 0.9773, 28.0313, 'C2H4'],
        (38, 2): [91, '(12C)H2(13C)H2', 0.02196, 29.034655, 'C2H4'],
        (39, 1): [92, '(12C)H3(16O)H', 0.98593, 32.026215, 'CH3OH'],
        (40, 1): [93, '(12C)H3(79Br)', 0.5013, 93.941811, 'CH3Br'],
        (40, 2): [94, '(12C)H3(81Br)', 0.48766, 95.939764, 'CH3Br'],
        (41, 1): [95, '(12C)H3(12C)(14N)', 0.97482, 41.026549, 'CH3CN'],
        (42, 1): [96, '(12C)(19F)4', 0.9893, 87.993616, 'CF4'],
        (43, 1): [116, '(12C)4H2', 0.955998, 50.01565, 'C4H2'],
        (44, 1): [109, 'H(12C)3(14N)', 0.9646069, 51.01089903687, 'HC3N'],
        (45, 1): [103, 'H2', 0.999688, 2.01565, 'H2'],
        (45, 2): [115, 'HD', 0.00022997, 3.021825, 'H2'],
        (46, 1): [97, '(12C)(32S)', 0.939624, 43.971036, 'CS'],
        (46, 2): [98, '(12C)(34S)', 0.0416817, 45.966787, 'CS'],
        (46, 3): [99, '(13C)(32S)', 0.0105565, 44.974368, 'CS'],
        (46, 4): [100, '(12C)(33S)', 0.00741668, 44.970399, 'CS'],
        (47, 1): [114, '(32S)(16O)3', 0.9423964, 79.95682, 'SO3'],
        (1001, 1): [101, 'H', None, None, 'H'],
        (1002, 1): [102, 'He', None, None, 'He'],
        (1018, 1): [104, 'Ar', None, None, 'Ar'],
    }

    def __init__(self, **kwargs):
        """
        Initialize a Hitran query class.
        """
        super().__init__()

    def _args_to_payload(self, *, molecule_number=1, isotopologue_number=1,
                         min_frequency=None, max_frequency=None):
        """
        Code to parse input and construct the payload dictionary.

        Parameters
        ----------
        molecule_number : int
            HITRAN molecule number
        isotopologue_number : int
            HITRAN isotopologue number
        min_frequency : `astropy.units`
            Minimum frequency (or any spectral() equivalent)
        max_frequency : `astropy.units`
            Maximum frequency (or any spectral() equivalent)

        Returns
        -------
        payload : dict
            Dictionary of the parameters to send to the SPLAT page

        """

        payload = dict()

        iso_id = str(self.ISO[(molecule_number,
                               isotopologue_number)][self.ISO_INDEX['id']])
        # mol_name = self.ISO[(molecule_number,
        #                      isotopologue_number)][self.ISO_INDEX['mol_name']]

        payload['iso_ids_list'] = iso_id

        if min_frequency is not None:
            min_frequency = min_frequency.to(u.cm**-1, u.spectral())

        if max_frequency is not None:
            max_frequency = max_frequency.to(u.cm**-1, u.spectral())

        if min_frequency is not None and max_frequency is not None:
            if min_frequency > max_frequency:
                min_frequency, max_frequency = max_frequency, min_frequency

        payload['numin'] = min_frequency.value
        payload['numax'] = max_frequency.value

        return payload

    @prepend_docstr_nosections("\n" + _args_to_payload.__doc__)
    def query_lines_async(self, *, get_query_payload=False, cache=True, **kwargs):
        """
        Queries Hitran class for a particular molecule with default arguments
        set. Based on fetch function from hapi.py.

        Returns
        -------
        response : `requests.Response`
            The response of the HTTP request.
        """

        params = self._args_to_payload(**kwargs)

        if get_query_payload:
            return params

        response = self._request(method='GET',
                                 url=self.QUERY_URL,
                                 params=params,
                                 timeout=self.TIMEOUT,
                                 cache=cache)

        return response

    def _parse_result(self, response, *, verbose=False):
        """
        Parse a response into an `~astropy.table.Table`
        """
        formats = parse_readme(self.FORMATFILE)

        dtypes = [entry['dtype'] for entry in formats.values()]

        rows = []
        for line in response.text.split('\n'):
            if line.strip():
                row = []
                start = 0
                for key, entry in formats.items():
                    formatter = entry['formatter']
                    length = entry['length']
                    value = formatter(line[start:start+length])
                    row.append(value)
                    start = start + length
                rows.append(row)

        result = Table(rows=rows, names=formats.keys(), dtype=dtypes)

        return result


Hitran = HitranClass()
