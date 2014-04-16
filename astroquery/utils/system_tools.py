import subprocess


#Import DEVNULL for py3 or py3
try:
    from subprocess import DEVNULL
except ImportError:
    import os
    DEVNULL = open(os.devnull, 'wb')

#Check availability of some system tools
#Exceptions are raised if not found
try:
    subprocess.call(["gzip", "-V"], stdout=DEVNULL)
except OSError:
    print("gzip was not found on your system! You should solve this issue before using astroquery.eso...")
    print("  On POSIX system: make sure gzip is in your path!")
    print("  On Windows: 7-zip (http://www.7-zip.org) should do the job, but unfortunately is not yet supported!")
    raise


def gunzip(filename):
    subprocess.call(["gzip", "-d", "{0}".format(filename)], stdout=DEVNULL)