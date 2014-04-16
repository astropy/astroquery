import subprocess


#Import DEVNULL for py3 or py3
try:
    from subprocess import DEVNULL
except ImportError:
    import os
    DEVNULL = open(os.devnull, 'wb')

#Check availability of some system tools
#Exceptions are raised if not found
subprocess.call(["gzip", "-V"], stdout=DEVNULL)


def gunzip(filename):
    subprocess.call(["gzip", "-d", "{0}".format(filename)], stdout=DEVNULL)