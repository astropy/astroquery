HITRAN2004
----------

The fields output for this profile are listed in order below with format strings, units and description the following information: :

molec_id
--------
C-style format specifier: %2d
Fortran-style format specifier: I2
Units: None
Description: The HITRAN integer ID for this molecule in all its isotopologue forms

local_iso_id
------------
C-style format specifier: %1d
Fortran-style format specifier: I1
Units: 
Description: Integer ID of a particular Isotopologue, unique only to a given molecule, in order or abundance (1 = most abundant)

nu
--
C-style format specifier: %12.6f
Fortran-style format specifier: F12.6
Units: cm-1
Description: Transition wavenumber

sw
--
C-style format specifier: %10.3e
Fortran-style format specifier: E10.3
Units: cm-1/(molec.cm-2)
Description: Line intensity, multiplied by isotopologue abundance, at T = 296 K

a
-
C-style format specifier: %10.3e
Fortran-style format specifier: E10.3
Units: s-1
Description: Einstein A-coefficient in s-1

gamma_air
---------
C-style format specifier: %5.4f
Fortran-style format specifier: F5.4
Units: cm-1.atm-1
Description: Air-broadened Lorentzian half-width at half-maximum at p = 1 atm and T = 296 K

gamma_self
----------
C-style format specifier: %5.3f
Fortran-style format specifier: F5.3
Units: cm-1.atm-1
Description: Self-broadened HWHM at 1 atm pressure and 296 K

elower
------
C-style format specifier: %10.4f
Fortran-style format specifier: F10.4
Units: cm-1
Description: Lower-state energy

n_air
-----
C-style format specifier: %4.2f
Fortran-style format specifier: F4.2
Units: 
Description: Temperature exponent for the air-broadened HWHM

delta_air
---------
C-style format specifier: %8.6f
Fortran-style format specifier: F8.6
Units: cm-1.atm-1
Description: Pressure shift induced by air, referred to p=1 atm

global_upper_quanta
-------------------
C-style format specifier: %15s
Fortran-style format specifier: A15
Units: None
Description: Electronic and vibrational quantum numbers and labels for the upper state of a transition

global_lower_quanta
-------------------
C-style format specifier: %15s
Fortran-style format specifier: A15
Units: None
Description: Electronic and vibrational quantum numbers and labels for the lower state of a transition

local_upper_quanta
------------------
C-style format specifier: %15s
Fortran-style format specifier: A15
Units: None
Description: Rotational, hyperfine and other quantum numbers and labels for the upper state of a transition

local_lower_quanta
------------------
C-style format specifier: %15s
Fortran-style format specifier: A15
Units: None
Description: Rotational, hyperfine and other quantum numbers and labels for the lower state of a transition

ierr1
-----
C-style format specifier: %1d
Fortran-style format specifier: I1
Units: 
Description: Ordered list of indices corresponding to uncertainty estimates of transition parameters

ierr2
-----
C-style format specifier: %1d
Fortran-style format specifier: I1
Units: 
Description: Ordered list of indices corresponding to uncertainty estimates of transition parameters

ierr3
-----
C-style format specifier: %1d
Fortran-style format specifier: I1
Units: 
Description: Ordered list of indices corresponding to uncertainty estimates of transition parameters

ierr4
-----
C-style format specifier: %1d
Fortran-style format specifier: I1
Units: 
Description: Ordered list of indices corresponding to uncertainty estimates of transition parameters

ierr5
-----
C-style format specifier: %1d
Fortran-style format specifier: I1
Units: 
Description: Ordered list of indices corresponding to uncertainty estimates of transition parameters

ierr6
-----
C-style format specifier: %1d
Fortran-style format specifier: I1
Units: 
Description: Ordered list of indices corresponding to uncertainty estimates of transition parameters

iref1
-----
C-style format specifier: %2d
Fortran-style format specifier: I2
Units: None
Description: Ordered list of reference identifiers for transition parameters

iref2
-----
C-style format specifier: %2d
Fortran-style format specifier: I2
Units: None
Description: Ordered list of reference identifiers for transition parameters

iref3
-----
C-style format specifier: %2d
Fortran-style format specifier: I2
Units: None
Description: Ordered list of reference identifiers for transition parameters

iref4
-----
C-style format specifier: %2d
Fortran-style format specifier: I2
Units: None
Description: Ordered list of reference identifiers for transition parameters

iref5
-----
C-style format specifier: %2d
Fortran-style format specifier: I2
Units: None
Description: Ordered list of reference identifiers for transition parameters

iref6
-----
C-style format specifier: %2d
Fortran-style format specifier: I2
Units: None
Description: Ordered list of reference identifiers for transition parameters

line_mixing_flag
----------------
C-style format specifier: %1s
Fortran-style format specifier: A1
Units: 
Description: A flag indicating the presence of additional data and code relating to line-mixing

gp
--
C-style format specifier: %7.1f
Fortran-style format specifier: F7.1
Units: None
Description: Upper state degeneracy

gpp
---
C-style format specifier: %7.1f
Fortran-style format specifier: F7.1
Units: None
Description: Lower state degeneracy

