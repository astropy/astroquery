# run client -w --upload=j_long_DWARF.1.1_coadd.fits
import os
import sys
from numpy import median, std
import astropy.io.fits as pyfits
import simplejson
from urllib import urlencode
from urllib2 import urlopen, Request
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.application  import MIMEApplication
from email.encoders import encode_noop
import time

import subprocess

sextractor_bin = "sex"
wget_bin = "wget"

image_name = sys.argv[1]


# Note that the pixel scale is a tightly set search constraint for 
# astrometry.net. For coadd mosaic pairitel images this is about 1 arcsec/pixel,
# but for triplestacks and reduced images this is about 2 arcsec/pixel.


sexcat_file = "test.sexcat"
anetcat_file = "test.anetcat"

cmd = (sextractor_bin + " " + image_name + 
    "[0] -c /Users/fred/mytoyz/users/admin/default.config " + 
    " -CATALOG_NAME " + sexcat_file)

print cmd

# Run source extractor

subprocess.call(cmd, shell=True)

# Read in and parse the source extractor catalog file.
# Columns are X, Y, FWHM_IMAGE, FLUX_APER, FLAGS
    # Eliminate flagged sources, or sources with weird FWHM
unflagged_sources = []
unflagged_fwhm_list = []
from astropy.table import Table
import numpy as np


sources = Table.read(sexcat_file, format='fits', hdu=1)

print sources

for line in np.array(sources).tolist():
    if line[4] == 0: # FLAGS
        #unflagged_sources.append([  float(line.split()[3]),     # FLUX_APER
        #                            float(line.split()[0]),     # X
        #                           float(line.split()[1]),     # Y
        #                           float(line.split()[2]) ])   # FWHM_IMAGE
        #unflagged_fwhm_list.append(float(line.split()[2]))
        unflagged_sources.append(list(line))
        unflagged_fwhm_list.append(line[3])

# Define lower and upper limits on acceptable FWHM (further weeds out bad sources)
med_fwhm = median(unflagged_fwhm_list)
std_fwhm = std(unflagged_fwhm_list)
fwhm_ll = median(unflagged_fwhm_list) - 2*std(unflagged_fwhm_list)
fwhm_ul = median(unflagged_fwhm_list) + 2*std(unflagged_fwhm_list)
# Enforce FWHM limits
final_source_list = []
for source in unflagged_sources:
    if source[3] > fwhm_ll and source[3] < fwhm_ul:
        final_source_list.append([  source[0],   # FLUX_APER
                                    source[1],   # X
                                    source[2]])  # Y
# Sort the final source list in decreasing flux
final_source_list.sort(reverse=True)

# Crop to the brightest 50 sources
if len(final_source_list) > 50:
    final_source_list = final_source_list[50:100]

print 'final source list', final_source_list

anetcat = file(anetcat_file, "w")
for source in final_source_list:
    anetcat.write('{0:.3f}\t{1:.3f}\n'.format(source[1], source[2]))
    #anetcat.write(str(round(source[1], 3)) + "\t" + str(round(source[2], 3)) + "\n")
    
anetcat.close()



# Now we interface with nova.astrometry.net
# First we retrieve the apikey from the environmental variables
upload_filename = anetcat_file

# Now we interface with nova.astrometry.net
# First we retrieve the apikey from the environmental variables

#apikey = os.environ.get('AN_API_KEY', None)

apikey = 'umrsuogflnslmldq'

if apikey is None:
    print 'You must set AN_API_KEY in your environment variables. Exiting.'
    os.system("rm " + anetcat_file)
    os.system("rm " + sexcat_file)
    sys.exit()

apiurl = 'http://nova.astrometry.net/api/'

# Login to the service
login_url = apiurl + "login"
login_args = { 'apikey' : apikey}
json = simplejson.dumps(login_args)
login_data = {'request-json': json}
login_data = urlencode(login_data)
login_headers = {}

request = Request(url=login_url, headers=login_headers, data=login_data)

f = urlopen(request)
txt = f.read()
result = simplejson.loads(txt)
stat = result.get('status')
if stat == 'error':
    print "Login error, exiting."
    os.system("rm " + anetcat_file)
    os.system("rm " + sexcat_file)
    sys.exit()
session_string = result["session"]


# Upload the text file to request a WCS solution
upload_url = apiurl + "upload"
upload_args = { 
                'allow_commercial_use': 'd', 
                'allow_modifications': 'd', 
                'publicly_visible': 'y', 
                'scale_units': 'arcsecperpix',
                'scale_type': 'ul', 
                'scale_lower': 0.20,       # arcsec/pix
                'scale_upper': 0.30,       # arcsec/pix
                'parity': 0,
                'session': session_string
                }
upload_json = simplejson.dumps(upload_args)


f = open(upload_filename, 'rb')
file_args=(upload_filename, f.read())

m1 = MIMEBase('text', 'plain')
m1.add_header('Content-disposition', 'form-data; name="request-json"')
m1.set_payload(upload_json)

m2 = MIMEApplication(file_args[1],'octet-stream',encode_noop)
m2.add_header('Content-disposition',
              'form-data; name="file"; filename="%s"' % file_args[0])

#msg.add_header('Content-Disposition', 'attachment',
# filename='bud.gif')
#msg.add_header('Content-Disposition', 'attachment',
# filename=('iso-8859-1', '', 'FuSballer.ppt'))

mp = MIMEMultipart('form-data', None, [m1, m2])

# Makie a custom generator to format it the way we need.
from cStringIO import StringIO
from email.generator import Generator

class MyGenerator(Generator):
    def __init__(self, fp, root=True):
        Generator.__init__(self, fp, mangle_from_=False,
                           maxheaderlen=0)
        self.root = root
    def _write_headers(self, msg):
        # We don't want to write the top-level headers;
        # they go into Request(headers) instead.
        if self.root:
            return                        
        # We need to use \r\n line-terminator, but Generator
        # doesn't provide the flexibility to override, so we
        # have to copy-n-paste-n-modify.
        for h, v in msg.items():
            print >> self._fp, ('%s: %s\r\n' % (h,v)),
        # A blank line always separates headers from body
        print >> self._fp, '\r\n',

    # The _write_multipart method calls "clone" for the
    # subparts.  We hijack that, setting root=False
    def clone(self, fp):
        return MyGenerator(fp, root=False)

fp = StringIO()
g = MyGenerator(fp)
g.flatten(mp)
upload_data = fp.getvalue()
upload_headers = {'Content-type': mp.get('Content-type')}

if False:
    print 'Sending headers:'
    print ' ', headers
    print 'Sending data:'
    print data[:1024].replace('\n', '\\n\n').replace('\r', '\\r')
    if len(data) > 1024:
        print '...'
        print data[-256:].replace('\n', '\\n\n').replace('\r', '\\r')
        print

print 'url', upload_url
print '\n\nheaders', upload_headers
print '\n\ndata', upload_data

print 'Sending request'

request = Request(url=upload_url, headers=upload_headers, data=upload_data)

f = urlopen(request)
txt = f.read()
result = simplejson.loads(txt)
stat = result.get('status')
if stat == 'error':
    print "Upload error, exiting."
    os.system("rm " + anetcat_file)
    os.system("rm " + sexcat_file)
    sys.exit()
submission_int = result["subid"]

print('stat', stat)
print('id', result['subid'])

time.sleep(15)

# Check submission status
subcheck_url = apiurl + "submissions/" + str(submission_int)

print 'subcheckurl', subcheck_url

request = Request(url=subcheck_url)
still_processing = True
n_failed_attempts = 0
while still_processing and n_failed_attempts < 5:
    try:
        f = urlopen(request)
        print 'f', f
        txt = f.read()
        print 'txt', txt
        result = simplejson.loads(txt)
        if result['jobs'][0] is None:
            print 'result is none'
            raise Exception()
        else:
            print result['jobs']
        # print result
        still_processing = False
    except:
        print "Submission doesn't exist yet, sleeping for 5s."
        time.sleep(5)
        n_failed_attempts += 1
if n_failed_attempts > 5:
    print "The submitted job has apparently timed out, exiting."
    #os.system("rm " + anetcat_file)
    #os.system("rm " + sexcat_file)
    sys.exit()

print 'result', result['jobs']

job_id_list = result["jobs"]
n_jobs = len(job_id_list)
time.sleep(5)

still_processing = True
n_failed_attempts = 0
n_failed_jobs = 0

while still_processing and n_failed_attempts < 12 and n_failed_jobs < n_jobs:
    time.sleep(5)
    for job_id in job_id_list:
        jobcheck_url = apiurl + "jobs/" + str(job_id)
        print(jobcheck_url)
        request = Request(url=jobcheck_url)
        f = urlopen(request)
        txt = f.read()
        result = simplejson.loads(txt)
        print "Checking astrometry.net job ID", job_id, result
        if result["status"] == "failure":
            print('failed')
            n_failed_jobs += 1
            job_id_list.remove(job_id)
        if result["status"] == "success":
            print('success')
            solved_job_id = job_id
            still_processing = False
            print job_id, "SOLVED"
    n_failed_attempts += 1

if still_processing == True:
    print "Astrometry.net took too long to process, so we're exiting."
    #os.system("rm " + anetcat_file)
    #os.system("rm " + sexcat_file)
    sys.exit()

if still_processing == False:
    import wget
    url = (wget_bin + " -q  --output-document=wcs.fits http://nova.astrometry.net/wcs_file/" + 
        str(solved_job_id))
    wget.download(url)


# Finally, strip out the WCS header info from this solved fits file and write it
# into the original fits file.

string_header_keys_to_copy = [
    "CTYPE1",
    "CTYPE2",
    "CUNIT1",
    "CUNIT2"
    ]

float_header_keys_to_copy = [
    "EQUINOX",
    "LONPOLE",
    "LATPOLE",
    "CRVAL1",
    "CRVAL2",
    "CRPIX1",
    "CRPIX2",
    "CD1_1",
    "CD1_2",
    "CD2_1",
    "CD2_2",
    "IMAGEW",
    "IMAGEH",
    "A_ORDER",
    "A_0_2",
    "A_1_1",
    "A_2_0",
    "B_ORDER",
    "B_0_2",
    "B_1_1",
    "B_2_0",
    "AP_ORDER",
    "AP_0_1",
    "AP_0_2",
    "AP_1_0",
    "AP_1_1",
    "AP_2_0",
    "BP_ORDER",
    "BP_0_1",
    "BP_0_2",
    "BP_1_0",
    "BP_1_1",
    "BP_2_0"
    ]
    

wcs_image = "wcs.fits"
wcs_hdu = pyfits.open(wcs_image)
wcs_header = wcs_hdu[0].header.copy()
wcs_hdu.close()


input_image = image_name
input_hdu = pyfits.open(input_image)
image_data = input_hdu[0].data
updated_imagefile_header = input_hdu[0].header.copy()
for hk in string_header_keys_to_copy:
    try:
        updated_imagefile_header.update(hk, wcs_header[hk])
    except:
        print hk, "string header update failed"
for hk in float_header_keys_to_copy:
    try:
        updated_imagefile_header.update(hk, float(wcs_header[hk]))
    except:
        print hk, "float header update failed"

updated_imagefile_header.update("AN_JOBID", str(solved_job_id))

output_hdu = pyfits.PrimaryHDU(image_data)
output_hdu.header = updated_imagefile_header

output_hdu.verify("fix")
output_hdulist = pyfits.HDUList([output_hdu])
output_hdulist.writeto(input_image.replace(".fits", ".wcs.fits"))
input_hdu.close()

#os.system("rm " + input_image)
#os.system("rm wcs.fits")
#os.system("mv " + input_image.replace(".fits", ".wcs.fits") + " " + input_image)
#os.system("rm " + anetcat_file)
#os.system("rm " + sexcat_file)

