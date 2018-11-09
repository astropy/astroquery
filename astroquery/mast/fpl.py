# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
MAST File Path Lookup
=====================

Functions to deal with mapping data products to storage paths

Due to the way that several missions work, we may need to check
more than one path per product
"""

def hst_paths(dataProduct):
    dataUri = dataProduct['dataURI']
    filename = dataUri.split("/")[-1]
    obs_id = dataProduct['obs_id']

    obs_id = obs_id.lower()

    # This next part is a bit funky.  Let me explain why:
    # We have 2 different possible URI schemes for HST:
    #   mast:HST/product/obs_id_filename.type (old style)
    #   mast:HST/product/obs_id/obs_id_filename.type (new style)
    # The first scheme was developed thinking that the obs_id in the filename
    # would *always* match the actual obs_id folder the file was placed in.
    # Unfortunately this assumption was false.
    # We have been trying to switch to the new uri scheme as it specifies the
    # obs_id used in the folder path correctly.
    # The cherry on top is that the obs_id in the new style URI is not always correct either!
    # When we are looking up files we have some code which iterates through all of
    # the possible permutations of the obs_id's last char which can be *ANYTHING*
    #
    # So in conclusion we can't trust the last char obs_id from the file or from the database
    # So with that in mind, hold your nose when reading the following:

    paths = []

    sane_path = os.path.join("hst", "public", obs_id[:4], obs_id, filename)
    paths += [sane_path]

    # Unfortunately our file placement logic is anything but sane
    # We put files in folders that don't make sense
    for ch in (string.digits + string.ascii_lowercase):
        # The last char of the obs_folder (observation id) can be any lowercase or numeric char
        insane_obs = obs_id[:-1] + ch
        insane_path = os.path.join("hst", "public", insane_obs[:4], insane_obs, filename)
        paths += [insane_path]

    return paths


def paths(dataProduct):
    if dataProduct['dataURI'].lower().startswith("mast:hst/product"):
        return fpl.hst_paths(dataProduct)

    return None
