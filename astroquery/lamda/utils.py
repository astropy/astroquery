import numpy as np
import re
from astropy import constants
from astropy import units as u


def ncrit(lamda_tables, transition_upper, transition_lower, temperature, OPR=3,
          partners=['H2', 'OH2', 'PH2']):
    """
    Compute the critical density for a transition given its temperature.

    The critical density is defined as the Einstein A value divided by the sum
    of the collision rates into the state minus the collision rates out of that
    state.  See Shirley et al 2015, eqn 4
    (http://esoads.eso.org/cgi-bin/bib_query?arXiv:1501.01629)

    Parameters
    ----------
    lamda_tables : list
        The list of LAMDA tables returned from a Lamda.query operation.
        Should be [ collision_rates_dict, Avals/Freqs, Energy Levels ]
    transition_upper : int
        The upper transition number as indexed in the lamda catalog
    transition_lower: int
        The lower transition number as indexed in the lamda catalog
    temperature : float
        Kinetic temperature in Kelvin.  Will be interpolated as appropriate.
        Extrapolation uses nearest value
    OPR : float
        ortho/para ratio of h2 if para/ortho h2 are included as colliders
    partners : list
        A list of valid partners.  It probably does not make sense to include
        both electrons and H2 because they'll have different densities.

    Returns
    -------
    ncrit : astropy.units.Quantity
        A quantity with units cm^-3
    """

    fortho = (OPR) / (OPR - 1)

    # exclude partners that are explicitly excluded
    crates = {coll: val for coll, val in lamda_tables[0].items()
              if coll in partners}
    avals = lamda_tables[1]
    enlevs = lamda_tables[2]

    aval = avals[(avals['Upper'] == transition_upper) &
                 (avals['Lower'] == transition_lower)]['EinsteinA'][0]

    temperature_re = re.compile(r"C_ij\(T=([0-9]*)\)")
    crate_temperatures = np.array(
        [int(temperature_re.search(cn).groups()[0])
         for cn in crates[list(crates.keys())[0]].keys()
         if temperature_re.search(cn)])

    if temperature < crate_temperatures.min():
        crates_ji_all = {
            coll: cr['C_ij(T={0})'.format(crate_temperatures.min())]
            for coll, cr in crates.items()}
    elif temperature > crate_temperatures.max():
        crates_ji_all = {
            coll: cr['C_ij(T={0})'.format(crate_temperatures.max())]
            for coll, cr in crates.items()}
    elif temperature in crate_temperatures:
        crates_ji_all = {coll: cr['C_ij(T={0})'.format(temperature)]
                         for coll, cr in crates.items()}
    else:  # interpolate
        nearest = np.argmin(np.abs(temperature - crate_temperatures))
        if crate_temperatures[nearest] < temperature:
            low, high = (crate_temperatures[nearest],
                         crate_temperatures[nearest + 1])
        else:
            low, high = (crate_temperatures[nearest - 1],
                         crate_temperatures[nearest])
        crates_ji_all = {coll:
                         (cr['C_ij(T={0})'.format(high)] -
                          cr['C_ij(T={0})'.format(low)]) *
                         (temperature - low) / (high - low) +
                         cr['C_ij(T={0})'.format(low)]
                         for coll, cr in crates.items()}

    transition_indices_ji = {
        coll: np.nonzero(cr['Upper'] == transition_upper)[0]
        for coll, cr in crates.items()}

    crates_ji = {coll: crates_ji_all[coll][transition_indices_ji[coll]]
                 for coll in crates}

    # i > j: collisions from higher levels
    transition_indices_ij = {
        coll: np.nonzero(cr['Lower'] == transition_upper)[0]
        for coll, cr in crates.items()}
    crates_ij = {}
    for coll in crates.keys():
        crates_ind = crates[coll][transition_indices_ij[coll]]
        degeneracies_i = enlevs['Weight'][crates_ind['Upper'] - 1]
        degeneracies_j = enlevs['Weight'][crates_ind['Lower'] - 1]
        energy_i = enlevs['Energy'][crates_ind['Upper'] - 1] * u.cm ** -1
        energy_j = enlevs['Energy'][crates_ind['Lower'] - 1] * u.cm ** -1
        # Shirley 2015 eqn 4:
        crates_ij[coll] = (
            crates_ji_all[coll][transition_indices_ij[coll]] *
            degeneracies_i / degeneracies_j.astype('float') *
            np.exp((-energy_i - energy_j).to(u.erg, u.spectral()) /
                   (constants.k_B * temperature * u.K)))

    crates_tot_percollider = {
        coll: (np.sum(crates_ij[coll]) + np.sum(crates_ji[coll])) *
        u.cm ** 3 / u.s for coll in crates}

    if 'OH2' in crates:
        crates_tot = (fortho * crates_tot_percollider['OH2'] +
                      (1 - fortho) * crates_tot_percollider['PH2'])
    elif 'PH2' in crates:
        crates_tot = crates_tot_percollider['PH2']
    elif 'H2' in crates:
        crates_tot = crates_tot_percollider['H2']

    return ((aval * u.s ** -1) / crates_tot).to(u.cm ** -3)
