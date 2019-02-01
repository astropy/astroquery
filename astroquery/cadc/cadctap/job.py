# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
=============
CadcTAP plus
=============

"""
import time
import requests
import astroquery.cadc.cadctap.jobSaxParser
from astroquery.utils.tap.model.job import Job
from astroquery.cadc.cadctap import utils

__all__ = ['Job']


class JobCadc(Job):
    """JobCadc class
    Reason for change
    -----------------
    Job class did not redirect
    """

    def __init__(self, async_job, query=None, connhandler=None):
        """Constructor

        Parameters
        ----------
        async_job : bool, mandatory
            'True' if the job is asynchronous
        query : str, optional, default None
            Query
        connhandler : TapConn, optional, default None
            Connection handler
        Reason for change
        -----------------
        Add errmessage for when a job errors
        """
        super(JobCadc, self).__init__(async_job=async_job,
                                      query=query,
                                      connhandler=connhandler)
        self.errmessage = None

    def get_results(self, verbose=False):
        """Returns the job results
        This method will block if the job is asynchronous and the job has not
        finished yet.

        Parameters
        ----------
        verbose : bool, optional, default 'False'
            flag to display information about the process

        Returns
        -------
        The job results (astropy.table).
        Reason for change
        -----------------
        Get rid of read from file because if file is wrong it errors badly
        """
        if self.results is not None:
            return self.results
        # Try to load from server: only async
        if not self.async_:
            # sync: result is in a file
            return None
        else:
            # async: result is in the server once the job is finished
            self.__load_async_job_results()
            return self.results

    def save_results(self, filename, verbose=False):
        """Saves job results
        If the job is asynchronous, this method will block until the results
        are available.

        Parameters
        ----------
        filename : str, mandatory
            name of the file to save the output to
        verbose : bool, optional, default 'False'
            flag to display information about the process
        Reason for change
        -----------------
        Add redirects if resutls are in a different place and get right
        output format for write()
        """
        output = filename
        output_format = self.parameters['format']
        if self._Job__resultInMemory:
            if output_format == 'csv':
                output_format = 'ascii.csv'
            elif "tsv" == output_format:
                output_format = "ascii.fast_tab"

            self.results.write(output, format=output_format)
        else:
            if not self.async_:
                # sync: cannot access server again
                if verbose:
                    print("No results to save")
            else:
                # Async
                self.wait_for_job_end(verbose)
                context = 'async/' + str(self.jobid) + "/results/result"
                response = self.connHandler.execute_get(context)
                if verbose:
                    print(response.status, response.reason)
                    print(response.getheaders())

                response = self.redirectJob(response, verbose)
                self.connHandler.dump_to_file(output, response)

    def wait_for_job_end(self, verbose=False):
        """Waits until a job is finished

        Parameters
        ----------
        verbose : bool, optional, default 'False'
            flag to display information about the process
        Reason for change
        -----------------
        Wait less for first few tries then wait longer and
        send abort if there is a keyboard interrupt
        """
        currentResponse = None
        responseData = None
        loops = 0
        while True:
            try:
                responseData = self.get_phase(update=True)
                currentResponse = self._Job__last_phase_response_status

                lphase = responseData.lower().strip()
                if verbose:
                    print("Job " + self.jobid + " status: " + lphase)
                if "pending" != lphase and "queued" != lphase and \
                        "executing" != lphase:
                    break
                # PENDING, QUEUED, EXECUTING, COMPLETED, ERROR, ABORTED,
                # UNKNOWN, HELD, SUSPENDED, ARCHIVED:
                if loops < 10:
                    seconds = 1
                else:
                    seconds = 30
                time.sleep(seconds)
            except KeyboardInterrupt:
                self.abortJob(verbose)
                raise
            loops = loops + 1
        return currentResponse, responseData

    def abortJob(self, verbose):
        """
        Reason for addding
        ------------------
        Abort the job if keyboard interrupt
        """
        if verbose:
            print('abbortting')
            print(self.jobid)
        args = {
            "PHASE": "ABORT"}
        data = self.connHandler.url_encode(args)
        response = self.connHandler.execute_post(
            'async/'+str(self.jobid)+'/phase',
            data)
        if verbose:
            print(response.status, response.reason)
            print(response.getheaders())
        return

    def __load_async_job_results(self, debug=False):
        """
        Reason for change
        -----------------
        Add getting the error reason and redirect for getting results
        """
        wjResponse, wjData = self.wait_for_job_end()
        if wjData != 'COMPLETED':
            if wjData == 'ERROR':
                subcontext = 'async/' + self.jobid
                errresponse = self.connHandler.execute_get(
                    subcontext)
                # parse job
                jsp = astroquery.cadc.cadctap.jobSaxParser. \
                    JobSaxParserCadc(async_job=False)
                errjob = jsp.parseData(errresponse)[0]
                errjob.connHandler = self.connHandler
                raise requests.exceptions.HTTPError(
                    errjob.errmessage)
            else:
                raise requests.exceptions.HTTPError(
                    'Error running query, PHASE: '+wjData)
        subContext = "async/" + str(self.jobid) + "/results/result"
        resultsResponse = self.connHandler.execute_get(subContext)
        if debug:
            print(resultsResponse.status, resultsResponse.reason)
            print(resultsResponse.getheaders())
        resultsResponse = self.redirectJob(resultsResponse, debug)
        outputFormat = self.parameters['format']
        results = utils.read_http_response(resultsResponse, outputFormat)
        self.set_results(results)
        self._Job__phase = wjData

    def redirectJob(self, resultsResponse, verbose=False):
        numberOfRedirects = 0
        while (resultsResponse.status == 303 or resultsResponse.status == 302)\
                and numberOfRedirects < 20:
            joblocation = self.connHandler.find_header(
                resultsResponse.getheaders(),
                "location")
            resultsResponse = self.connHandler.execute_get_other(joblocation)
            numberOfRedirects += 1
            if verbose:
                print(resultsResponse.status, resultsResponse.reason)
                print(resultsResponse.getheaders())

        isError = self.connHandler.check_launch_response_status(
            resultsResponse,
            verbose,
            200)
        if isError:
            if verbose:
                print(resultsResponse.reason)
            raise Exception(resultsResponse.reason)
        else:
            return resultsResponse
