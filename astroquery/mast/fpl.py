# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
MAST File Path Lookup
=====================

Functions to deal with mapping data products to storage paths

Due to the way that several missions work, we may need to check
more than one path per product
"""

import string


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

    sane_path = "/".join(["hst", "public", obs_id[:4], obs_id, filename])
    paths += [sane_path]

    # Unfortunately our file placement logic is anything but sane
    # We put files in folders that don't make sense
    for ch in (string.digits + string.ascii_lowercase):
        # The last char of the obs_folder (observation id) can be any lowercase or numeric char
        insane_obs = obs_id[:-1] + ch
        insane_path = "/".join(["hst", "public", insane_obs[:4], insane_obs, filename])
        paths += [insane_path]

    return paths


def _tess_product_paths(file_name):
    """ TESS Product File """
    # tess2018206045859-s0001-0000000206409997-0120-s_tp.fits
    # s0001-0000 0002 0640 9997
    # s0001/0000/0002/0640/9997
    # sssss/zzzz/ffff/pppp/llll
    # 18-23 24 28   32   36  40

    sssss = file_name[18:23]
    zzzz = file_name[24:28]
    ffff = file_name[28:32]
    pppp = file_name[32:36]
    llll = file_name[36:40]

    parts = [
        "tess",
        "public",
        "tid",
        sssss,
        zzzz,
        ffff,
        pppp,
        llll,
        file_name
    ]

    return ["/".join(parts)]


def _tess_report_paths(file_name):
    """ TESS Report File """
    # tess2018206190142-s0001-s0001-0000000349518145-01-00106_dvs.pdf
    #                   sssss eeeee zzzzffffppppllll
    #                   18-23 24-29 30  34  38  42  46

    # sssss = file_name[18:23]
    eeeee = file_name[24:29]
    zzzz = file_name[30:34]
    ffff = file_name[34:38]
    pppp = file_name[38:42]
    llll = file_name[42:46]

    parts = [
        "tess",
        "public",
        "tid",
        eeeee,
        zzzz,
        ffff,
        pppp,
        llll,
        file_name
    ]

    return ["/".join(parts)]


def _tess_ffi_file(file_name):
    """ TESS FFI File """
    # tess2018229142941-s0001-4-3-0120-s_ffic.fits
    #     yyyyddd       sssss ccc
    # s0001/2018/229/4-3
    # 18-23 4-8 8-11 24-27

    sector = file_name[18:23]
    year = file_name[4:8]
    day_number = file_name[8:11]
    camera_chip = file_name[24:27]

    parts = [
        "tess",
        "public",
        "ffi",
        sector,
        year,
        day_number,
        camera_chip,
        file_name
    ]
    return ["/".join(parts)]


_tess_map = {
    _tess_product_paths: ["tp.fits", "lc.fits"],
    _tess_report_paths: ["_dvs.pdf", "_dvr.pdf", "_dvr.xml", "_dvt.fits"],
    _tess_ffi_file: ['ffir.fits', 'ffic.fits', 'col.fits', 'cbv.fits'],
}


def tess_paths(dataProduct):
    dataUri = dataProduct['dataURI']
    filename = dataUri.split("/")[-1]

    for paths_fn, suffixes in _tess_map.items():
        for suffix in suffixes:
            if filename.lower().endswith(suffix):
                return paths_fn(filename)

    return None


def paths(dataProduct):
    if dataProduct['dataURI'].lower().startswith("mast:hst/product"):
        return hst_paths(dataProduct)

    if dataProduct['dataURI'].lower().startswith("mast:tess/product"):
        return tess_paths(dataProduct)

    return None


def has_path(dataProduct):
    return dataProduct['dataURI'].lower().startswith("mast:hst/product") or \
            dataProduct['dataURI'].lower().startswith("mast:tess/product")
