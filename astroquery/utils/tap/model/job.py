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
from urllib.parse import urlencode

from astroquery.utils.tap.model import modelutils
from astroquery.utils.tap.xmlparser import utils
from astroquery.utils.tap import taputils
from astropy.logger import log
import requests


__all__ = ['Job']


class Job:
    """Job class
    """

    def __init__(self, async_job, *, query=None, connhandler=None):
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
        self.outputFileUser = None
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

    def set_phase(self, phase):
        """Sets the job phase

        Parameters
        ----------
        phase : str, mandatory
            job phase
        """
        if self.is_finished():
            raise ValueError("Cannot assign a phase when a job is finished")
        self._phase = phase

    def start(self, *, verbose=False):
        """Starts the job (allowed in PENDING phase only)

        Parameters
        ----------
        verbose : bool, optional, default 'False'
            flag to display information about the process
        """
        self.__change_phase(phase="RUN", verbose=verbose)

    def abort(self, *, verbose=False):
        """Aborts the job (allowed in PENDING phase only)

        Parameters
        ----------
        verbose : bool, optional, default 'False'
            flag to display information about the process
        """
        self.__change_phase(phase="ABORT", verbose=verbose)

    def __change_phase(self, phase, *, verbose=False):
        if self._phase == 'PENDING':
            context = f"async/{self.jobid}/phase"
            response = self.connHandler.execute_tappost(
                subcontext=context, data=urlencode({"PHASE": phase}), verbose=verbose
            )
            if verbose:
                print(response.status, response.reason)
                print(response.getheaders())
            self.__last_phase_response_status = response.status
            if phase == 'RUN':
                # a request for RUN does not mean the server executes the job
                phase = 'QUEUED'
                if response.status != 200 and response.status != 303:
                    errMsg = taputils.get_http_response_error(response)
                    print(response.status, errMsg)
                    raise requests.exceptions.HTTPError(errMsg)
            else:
                if response.status != 200:
                    errMsg = taputils.get_http_response_error(response)
                    print(response.status, errMsg)
                    raise requests.exceptions.HTTPError(errMsg)
            self._phase = phase
            return response
        else:
            raise ValueError(f"Cannot start a job in phase: {self._phase}")

    def send_parameter(self, *, name=None, value=None, verbose=False):
        """Sends a job parameter (allowed in PENDING phase only).

        Parameters
        ----------
        name : string
            Parameter name.
        value : string
            Parameter value.
        """
        if self._phase == 'PENDING':
            # send post parameter/value
            context = f"async/{self.jobid}"
            response = self.connHandler.execute_tappost(subcontext=context,
                                                        data=urlencode({name: value}),
                                                        verbose=verbose)
            if verbose:
                print(response.status, response.reason)
                print(response.getheaders())
            self.__last_phase_response_status = response.status
            if response.status != 200:
                errMsg = taputils.get_http_response_error(response)
                print(response.status, errMsg)
                raise requests.exceptions.HTTPError(errMsg)
            return response
        else:
            raise ValueError(f"Cannot start a job in phase: {self._phase}")

    def get_phase(self, *, update=False):
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
            phase_request = f"async/{self.jobid}/phase"
            response = self.connHandler.execute_tapget(phase_request)

            self.__last_phase_response_status = response.status
            if response.status != 200:
                errMsg = taputils.get_http_response_error(response)
                print(response.status, errMsg)
                raise requests.exceptions.HTTPError(errMsg)

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
        # read_results_table_from_file checks whether
        # the file already exists or not
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

    def save_results(self, *, verbose=False):
        """Saves job results
        If the job is asynchronous, this method will block until the results
        are available.

        Parameters
        ----------
        verbose : bool, optional, default 'False'
            flag to display information about the process
        """
        if self.__resultInMemory:
            if verbose:
                print(f"Saving results to: {self.outputFile}")
            self.results.to_xml(self.outputFile)
        else:
            if not self.async_:
                # sync: cannot access server again
                log.info("No results to save")
            else:
                # Async
                self.wait_for_job_end(verbose=verbose)
                response = self.connHandler.execute_tapget(
                    f"async/{self.jobid}/results/result")
                if verbose:
                    print(response.status, response.reason)
                    print(response.getheaders())
                isError = self.connHandler.\
                    check_launch_response_status(response,
                                                 verbose,
                                                 200)
                if isError:
                    print(response.reason)
                    raise Exception(response.reason)
                if self.outputFileUser is None:
                    # User did not provide an output
                    # The output is a temporary one, analyse header
                    self.outputFile = taputils.get_suitable_output_file(
                        self.connHandler, True, None, response.getheaders(),
                        False, self.parameters['format'])
                    output = self.outputFile
                else:
                    output = self.outputFileUser
                if verbose:
                    print(f"Saving results to: {output}")
                self.connHandler.dump_to_file(output, response)

    def wait_for_job_end(self, *, verbose=False):
        """Waits until a job is finished

        Parameters
        ----------
        verbose : bool, optional, default 'False'
            flag to display information about the process
        """
        currentResponse = None
        responseData = None
        lphase = None
        # execute job if not running
        if self._phase == 'PENDING':
            log.info("Job in PENDING phase, sending phase=RUN request.")
            try:
                self.start(verbose=verbose)
            except Exception as ex:
                # ignore
                if verbose:
                    print("Exception when trying to start job", ex)
        while True:
            responseData = self.get_phase(update=True)
            currentResponse = self.__last_phase_response_status

            lphase = responseData.upper().strip()
            if verbose:
                print(f"Job {self.jobid} status: {lphase}")
            if ("PENDING" != lphase and "QUEUED" != lphase and "EXECUTING" != lphase):
                break
            # PENDING, QUEUED, EXECUTING, COMPLETED, ERROR, ABORTED, UNKNOWN,
            # HELD, SUSPENDED, ARCHIVED:
            time.sleep(0.5)
        return currentResponse, lphase

    def __load_async_job_results(self, *, debug=False):
        wjResponse, phase = self.wait_for_job_end()
        subContext = f"async/{self.jobid}/results/result"
        resultsResponse = self.connHandler.execute_tapget(subContext)
        # resultsResponse = self.__readAsyncResults(self.__jobid, debug)
        if debug:
            print(resultsResponse.status, resultsResponse.reason)
            print(resultsResponse.getheaders())

        resultsResponse = self.__handle_redirect_if_required(resultsResponse,
                                                             verbose=debug)
        isError = self.connHandler.\
            check_launch_response_status(resultsResponse,
                                         debug,
                                         200)
        self._phase = phase
        if phase == 'ERROR':
            errMsg = self.get_error(verbose=debug)
            raise SystemError(errMsg)
        else:
            if isError:
                errMsg = taputils.get_http_response_error(resultsResponse)
                print(resultsResponse.status, errMsg)
                raise requests.exceptions.HTTPError(errMsg)
            else:
                outputFormat = self.parameters['format']
                results = utils.read_http_response(resultsResponse,
                                                   outputFormat)
                self.set_results(results)

    def __handle_redirect_if_required(self, resultsResponse, *, verbose=False):
        # Thanks @emeraldTree24
        numberOfRedirects = 0
        while ((resultsResponse.status == 303 or resultsResponse.status == 302) and numberOfRedirects < 20):
            joblocation = self.connHandler.\
                find_header(resultsResponse.getheaders(), "location")
            if verbose:
                print(f"Redirecting to: {joblocation}")
            resultsResponse = self.connHandler.execute_tapget(joblocation)
            numberOfRedirects += 1
            if verbose:
                print(resultsResponse.status, resultsResponse.reason)
                print(resultsResponse.getheaders())
        return resultsResponse

    def get_error(self, *, verbose=False):
        """Returns the error associated to a job

        Parameters
        ----------
        verbose : bool, optional, default 'False'
            flag to display information about the process

        Returns
        -------
        The job error.
        """
        subContext = f"async/{self.jobid}/error"
        resultsResponse = self.connHandler.execute_tapget(subContext)
        # resultsResponse = self.__readAsyncResults(self.__jobid, debug)
        if verbose:
            print(resultsResponse.status, resultsResponse.reason)
            print(resultsResponse.getheaders())
        if (resultsResponse.status != 200 and resultsResponse.status != 303 and resultsResponse.status != 302):
            errMsg = taputils.get_http_response_error(resultsResponse)
            print(resultsResponse.status, errMsg)
            raise requests.exceptions.HTTPError(errMsg)
        else:
            if resultsResponse.status == 303 or resultsResponse.status == 302:
                # get location
                location = self.connHandler.\
                    find_header(resultsResponse.getheaders(), "location")
                if location is None:
                    raise requests.exceptions.HTTPError("No location found after redirection was received (303)")
                if verbose:
                    print(f"Redirect to {location}")
                # load
                relativeLocation = self.__extract_relative_location(location, self.jobid)
                relativeLocationSubContext = f"async/{self.jobid}/{relativeLocation}"
                response = self.connHandler.\
                    execute_tapget(relativeLocationSubContext)
                response = self.__handle_redirect_if_required(response,
                                                              verbose=verbose)
                isError = self.connHandler.\
                    check_launch_response_status(response, verbose, 200)
                if isError:
                    errMsg = taputils.get_http_response_error(resultsResponse)
                    print(resultsResponse.status, errMsg)
                    raise requests.exceptions.HTTPError(errMsg)
            else:
                response = resultsResponse
            errMsg = taputils.get_http_response_error(response)
        return errMsg

    def is_finished(self):
        """Returns whether the job is finished (ERROR, ABORTED, COMPLETED) or not

        """
        if (self._phase == 'ERROR' or self._phase == 'ABORTED' or self._phase == 'COMPLETED'):
            return True
        else:
            return False

    def __extract_relative_location(self, location, jobid):
        """Extracts uws subpath from location.

        Parameters
        ----------
        location : str, mandatory
            A 303 redirection header

        Returns
        -------
        The relative location.
        """
        pos = location.find(jobid)
        if pos < 0:
            return location
        pos += len(str(jobid))
        # skip '/'
        pos += 1
        return location[pos:]

    def __str__(self):
        if self.results is None:
            result = "None"
        else:
            result = self.results.info()
        return f"Jobid: {self.jobid}" \
            f"\nPhase: {self._phase}" \
            f"\nOwner: {self.ownerid}" \
            f"\nOutput file: {self.outputFile}" \
            f"\nResults: {result}"
