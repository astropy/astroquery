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

import time

from astroquery.utils.tap.model import modelutils
from astroquery.utils.tap.xmlparser import utils

__all__ = ['Job']


class Job(object):
    """Job class
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
        """
        # async is a reserved keyword starting python 3.7
        self.async_ = async_job
        self.connHandler = None
        self.isFinished = None
        self.jobid = None
        self.remoteLocation = None
        # phase is actually indended to be private as get_phase is non-trivial
        self._phase = None
        self.outputFile = None
        self.responseStatus = 0
        self.responseMsg = None
        self.results = None
        self.__resultInMemory = False    # only used within class
        self.failed = False
        self.runid = None
        self.ownerid = None
        self.startTime = None
        self.endTime = None
        self.creationTime = None
        self.executionDuration = None
        self.destruction = None
        self.locationId = None
        self.name = None
        self.quote = None

        self.connHandler = connhandler
        self.parameters = {}
        self.parameters['query'] = query
        # default output format
        self.parameters['format'] = 'votable'

    def get_phase(self, update=False):
        """Returns the job phase. May optionally update the job's phase.

        Parameters
        ----------
        update : bool
            if True, the phase will by updated by querying the server before
            returning.

        Returns
        -------
        The job phase
        """
        if update:
            phase_request = "async/"+str(self.jobid)+"/phase"
            response = self.connHandler.execute_get(phase_request)

            self.__last_phase_response_status = response.status
            if response.status != 200:
                raise Exception(response.reason)

            self._phase = str(response.read().decode('utf-8'))

        return self._phase

    def set_response_status(self, status, msg):
        """Sets the HTTP(s) connection status

        Parameters
        ----------
        status : int, mandatory
            HTTP(s) response status
        msg : str, mandatory
            HTTP(s) response message
        """
        self.__responseStatus = status
        self.__responseMsg = msg

    def get_data(self):
        """Returns the job results (Astroquery API specification)
        This method will block if the job is asynchronous and the job has not
        finished yet.

        Returns
        -------
        The job results (astropy.table).
        """
        return self.get_results()

    def get_results(self):
        """Returns the job results
        This method will block if the job is asynchronous and the job has not
        finished yet.

        Returns
        -------
        The job results (astropy.table).
        """
        if self.results is not None:
            return self.results
        # try load results from file
        # read_results_table_from_file checks whether the file already exists or not
        outputFormat = self.parameters['format']
        results = modelutils.read_results_table_from_file(self.outputFile,
                                                          outputFormat)
        if results is not None:
            self.results = results
            return results
        # Try to load from server: only async
        if not self.async_:
            # sync: result is in a file
            return None
        else:
            # async: result is in the server once the job is finished
            self.__load_async_job_results()
            return self.results

    def set_results(self, results):
        """Sets the job results

        Parameters
        ----------
        results : Table object, mandatory
            job results
        """
        self.results = results
        self.__resultInMemory = True

    def save_results(self, verbose=False):
        """Saves job results
        If the job is asynchronous, this method will block until the results
        are available.

        Parameters
        ----------
        verbose : bool, optional, default 'False'
            flag to display information about the process
        """
        output = self.outputFile
        if self.__resultInMemory:
            self.results.to_xml(output)
        else:
            if not self.async_:
                # sync: cannot access server again
                print("No results to save")
            else:
                # Async
                self.wait_for_job_end(verbose)
                response = self.connHandler.execute_get(
                    "async/"+str(self.jobid)+"/results/result")
                if verbose:
                    print(response.status, response.reason)
                    print(response.getheaders())
                isError = self.connHandler.check_launch_response_status(response,
                                                                          verbose,
                                                                          200)
                if isError:
                    print(response.reason)
                    raise Exception(response.reason)
                self.connHandler.dump_to_file(output, response)

    def wait_for_job_end(self, verbose=False):
        """Waits until a job is finished

        Parameters
        ----------
        verbose : bool, optional, default 'False'
            flag to display information about the process
        """
        currentResponse = None
        responseData = None
        while True:
            responseData = self.get_phase(update=True)
            currentResponse = self.__last_phase_response_status

            lphase = responseData.lower().strip()
            if verbose:
                print("Job " + self.jobid + " status: " + lphase)
            if "pending" != lphase and "queued" != lphase and "executing" != lphase:
                break
            # PENDING, QUEUED, EXECUTING, COMPLETED, ERROR, ABORTED, UNKNOWN,
            # HELD, SUSPENDED, ARCHIVED:
            time.sleep(0.5)
        return currentResponse, responseData

    def __load_async_job_results(self, debug=False):
        wjResponse, wjData = self.wait_for_job_end()
        subContext = "async/" + str(self.jobid) + "/results/result"
        resultsResponse = self.connHandler.execute_get(subContext)
        # resultsResponse = self.__readAsyncResults(self.__jobid, debug)
        if debug:
            print(resultsResponse.status, resultsResponse.reason)
            print(resultsResponse.getheaders())
        isError = self.connHandler.check_launch_response_status(resultsResponse,
                                                                  debug,
                                                                  200)
        if isError:
            print(resultsResponse.reason)
            raise Exception(resultsResponse.reason)
        else:
            outputFormat = self.parameters['format']
            results = utils.read_http_response(resultsResponse, outputFormat)
            self.set_results(results)
            self._phase = wjData

    def __str__(self):
        if self.results is None:
            result = "None"
        else:
            result = self.results.info()
        return "Jobid: " + str(self.jobid) + \
            "\nPhase: " + str(self._phase) + \
            "\nOwner: " + str(self.ownerid) + \
            "\nOutput file: " + str(self.outputFile) + \
            "\nResults: " + str(result)
