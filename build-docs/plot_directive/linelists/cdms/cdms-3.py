import numpy as np
import matplotlib.pyplot as plt
from astroquery.linelists.cdms import CDMS
from scipy.optimize import curve_fit

result = CDMS.get_species_table()
mol = result[result['tag'] == 30501]  # do not include signs of tag for this
def f(T, a):
    return np.log10(a*T**(1.5))
keys = [k for k in mol.keys() if 'lg' in k]
def tryfloat(x):
    try:
        return float(x)
    except:
        return np.nan
temp = np.array([float(k.split('(')[-1].split(')')[0]) for k in keys])
part = np.array([tryfloat(x) for x in mol[keys][0]])
param, cov = curve_fit(f, temp[np.isfinite(part)], part[np.isfinite(part)])
x = np.linspace(2.7,500)
y = f(x,param[0])
inds = np.argsort(temp)
interp_Q = np.interp(x, temp[inds], 10**part[inds])

plt.clf()
plt.plot(x, (10**y-interp_Q)/10**y)
plt.xlabel("Temperature")
plt.ylabel("Fractional difference between linear and fitted")