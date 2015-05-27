import numpy as np
import re
from astropy import constants
from astropy import units as u

def ncrit(lamda_tables, transition_upper, transition_lower, temperature, OPR=3,):
    """

    """
    
    fortho = (OPR)/(OPR-1)

    crates = lamda_tables[0]
    avals = lamda_tables[1]
    enlevs = lamda_tables[2]

    aval = avals[(avals['Upper']==transition_upper) &
                 (avals['Lower']==transition_lower)]['EinsteinA'][0]

    temperature_re = re.compile("C_ij\(T=([0-9]*)\)")
    crate_temperatures = np.array([int(temperature_re.search(cn).groups()[0])
                                   for cn in crates[crates.keys()[0]].keys()
                                   if temperature_re.search(cn)
                         ])
    if temperature < crate_temperatures.min():
        crates_ji_all = {coll: cr['C_ij(T={0})'.format(crate_temperatures.min())]
                         for coll,cr in crates.items()}
    elif temperature > crate_temperatures.max():
        crates_ji_all = {coll: cr['C_ij(T={0})'.format(crate_temperatures.max())]
                         for coll,cr in crates.items()}
    elif temperature in crate_temperatures:
        crates_ji_all = {coll: cr['C_ij(T={0})'.format(temperature)]
                         for coll,cr in crates.items()}
    else: # interpolate
        nearest = np.argmin(np.abs(temperature-crate_temperatures))
        if crate_temperatures[nearest] < temperature:
            low, high = crate_temperatures[nearest], crate_temperatures[nearest+1]
        else:
            low, high = crate_temperatures[nearest-1], crate_temperatures[nearest]
        crates_ji_all = {coll: 
                              (cr['C_ij(T={0})'.format(high)]-cr['C_ij(T={0})'.format(low)])*(temperature-low)/(high-low)
                               +cr['C_ij(T={0})'.format(low)]
                         for coll,cr in crates.items()}

    transition_indices_ji = {coll: np.nonzero(cr['Upper']==transition_upper)[0] for coll,cr in crates.items()}
    crates_ji = {coll: crates_ji_all[coll][transition_indices_ji[coll]]
                 for coll in crates}


    # i > j: collisions from higher levels
    transition_indices_ij = {coll: np.nonzero(cr['Lower']==transition_upper)[0] for coll,cr in crates.items()}
    coll = crates.keys()[0]
    degeneracies_i = enlevs['Weight'][crates[coll][transition_indices_ij[coll]]['Upper']-1]
    degeneracies_j = enlevs['Weight'][crates[coll][transition_indices_ij[coll]]['Lower']-1]
    energy_i = enlevs['Energy'][crates[coll][transition_indices_ij[coll]]['Upper']-1] *u.cm**-1
    energy_j = enlevs['Energy'][crates[coll][transition_indices_ij[coll]]['Lower']-1] *u.cm**-1
    # Shirley 2015 eqn 4:
    crates_ij = {coll: (crates_ji_all[coll][transition_indices_ij[coll]] * degeneracies_i/degeneracies_j.astype('float')
                       * np.exp((-energy_i-energy_j).to(u.erg, u.spectral())/(constants.k_B * temperature * u.K)))
                 for coll in crates}

    crates_tot_percollider = {coll: (np.sum(crates_ij[coll]) + np.sum(crates_ji[coll])) * u.cm**3/u.s
                              for coll in crates}
    if 'OH2' in crates:
        crates_tot = fortho*crates_tot_percollider['OH2'] + (1-fortho)*crates_tot_percollider['PH2']
    elif 'H2' in crates:
        crates_tot = crates_tot_percollider['H2']


    return ((aval*u.s**-1) / crates_tot).to(u.cm**-3)
