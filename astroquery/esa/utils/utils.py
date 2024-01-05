"""
==============================
ESA Utils for common functions
==============================

European Space Astronomy Centre (ESAC)
European Space Agency (ESA)

"""

import os


def check_rename_to_gz(filename):
    rename = False
    if os.path.exists(filename):
        with open(filename, 'rb') as test_f:
            if test_f.read(2) == b'\x1f\x8b' and not filename.endswith('.fits.gz'):
                rename = True

    if rename:
        output = os.path.splitext(filename)[0] + '.fits.gz'
        os.rename(filename, output)
        return os.path.basename(output)
    else:
        return os.path.basename(filename)
