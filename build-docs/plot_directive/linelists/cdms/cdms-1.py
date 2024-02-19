import numpy as np
import matplotlib.pyplot as plt
from astroquery.linelists.cdms import CDMS

result = CDMS.get_species_table()
mol = result[result['tag'] == 28503]  # do not include signs of tag for this
keys = [k for k in mol.keys() if 'lg' in k]
temp = np.array([float(k.split('(')[-1].split(')')[0]) for k in keys])
part = list(mol[keys][0])
plt.scatter(temp,part)
plt.xlabel('Temperature (K)')
plt.ylabel('Partition Function Value')
plt.title('Partition Function vs Temperature')