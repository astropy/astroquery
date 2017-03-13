# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
=============
TAP plus
=============

@author: Juan Carlos Segovia
@contact: juan.carlos.segovia@sciops.esa.int

European Space Astronomy Centre (ESAC)
European Space Agency (ESA)

Created on 30 jun. 2016


"""

import os

from astroquery.utils.tap.core import TapPlus


def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


gaia = TapPlus("http://gea.esac.esa.int/tap-server/tap")


#import in python console without installing module:
# >>> import sys
# >>> import os
# #provide the location (directory) of the Gaia TAP plus code
# >>> sys.path.append(os.path.abspath('/abs_path_to_module/gaia-py-tap'))
# >>> from tap.core import TapPlus
# >>> 


#Getting the tables

#To obtain the available tables, type:

tables = gaia.load_tables(only_names=True)
for table in (tables):
    print (table.get_qualified_name())

print ("\n\n")

#Now, to get the columns of gaiadr1.gaia_source table:

gaiadr1_table = gaia.load_table('gaiadr1.gaia_source')

print (gaiadr1_table)

for column in (gaiadr1_table.get_columns()):
    print (column.get_name())


#To request for the columns I am interested on

#Synchronous job
job = gaia.launch_job("select top 100 \
solution_id,ref_epoch,ra_dec_corr,astrometric_n_obs_al,matched_observations,duplicated_source,phot_variable_flag \
from gaiadr1.gaia_source order by source_id")

#If you want to dump the results into a file add: dump_to_file=True
#job = gaia.launch_job("select top 100 \
#solution_id,ref_epoch,ra_dec_corr,astrometric_n_obs_al,matched_observations,duplicated_source,phot_variable_flag \
#from gaiadr1.gaia_source order by source_id", dump_to_file=True)


print (job)
r = job.get_results()
print (r['solution_id'])


#Async job (all columns)
job = gaia.launch_job_async("select top 100 * from gaiadr1.gaia_source order by source_id")

#If you want to dump the results into a file add: dump_to_file=True
#job = gaia.launch_job_async("select top 100 * from gaiadr1.gaia_source order by source_id", dump_to_file=True)


print (job)
r = job.get_results()
print (r['solution_id'])


#Load a job using its identifier
jobid = job.get_jobid()
j = gaia.load_async_job(jobid)
print (j)
r = j.get_results()
print (r['solution_id'])


#list asynchronous jobs
jobs = gaia.list_async_jobs()
print ("Jobs async list:")
if jobs is None:
    print ("No jobs")
else:
    print (jobs)


#Upload
upload_resource = data_path('test_upload.vot')
j = gaia.launch_job(query="select * from tap_upload.table_test", upload_resource=upload_resource, upload_table_name="table_test", verbose=True)
r = j.get_results()
r.pprint()

#Remove
job = gaia.launch_job_async("select top 100 * from gaiadr1.gaia_source order by source_id")
r = job.get_results()
gaia.remove_jobs([job.get_jobid()])

#PRIVATE ACCESS
#Access to a user job 
jobid = "1475656076126O"
try:
    j = gaia.load_async_job(jobid)
except Exception as e:
    print ("Expected unauthorized exception: " + str(e))

gaia.login_gui()
#You can use a file: one line for user, the next one for password
#gaia.login(file="mycredentials.file")

j = gaia.load_async_job(jobid)

print (j)


#It is possible to use TapPlus to connect to a different tap server:
#TapPlus is fully compatible with TAP specification
#from gaia.tapplus.tap import TapPlus
#tap = TapPlus(url="http://TAPVizieR.u-strasbg.fr/TAPVizieR/tap")
##Inspect tables
#tables = tap.load_tables()
#for table in (tables):
#    print (table.get_name())
##Launch sync job
#job = tap.launch_job("SELECT top 10 * from " + tables[0].get_name())
#r = job.get_results()
#r.pprint()

#Example2
#from gaia.tapplus.tap import TapPlus
#tap = TapPlus(url="http://irsa.ipac.caltech.edu/TAP")
#job = tap.launch_job_async("SELECT TOP 10 * FROM fp_psc")
#r = job.get_results()
#r.pprint()


print ("end")