import subprocess
import sys
from distutils import LooseVersion


def get_latest_pip_version():
    pipes = subprocess.Popen([sys.executable, '-m', 'pip', 'install', 'astroquery=='],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    std_out, std_err = pipes.communicate()

    std_err = std_err.decode()

    version_string_list = [x.strip(",").strip(")") for x in
                           std_err.split("\n")[0].split("from versions: ")[1].split()]

    # make the version list sortable by making dev >>> other
    version_list = [LooseVersion(x.replace("dev","999.")) for x in version_string_list]

    # remove any versions that were 0.0.dev, they don't match.
    # (this is a total hack that we shouldn't have to do)
    while version_list[-1].version[2] == 999:
        version_list.pop(-1)

    latest_version = str(version_list[-1]).replace("999.","dev")

    return latest_version
