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
from pathlib import Path

import pytest
from astropy.io.votable import from_table
from astropy.table import Table
from astropy.utils.data import get_pkg_data_filename

from astroquery.utils.tap.conn.tests.DummyConnHandler import DummyConnHandler
from astroquery.utils.tap.conn.tests.DummyResponse import DummyResponse
from astroquery.utils.tap.model.job import Job

package = "astroquery.utils.tap.model.tests"


def test_job_basic():
    with pytest.raises(AttributeError):
        job = Job(async_job=True)
        job.get_results()


@pytest.mark.parametrize("extension, output_format",
                         [('.vot.gz', 'votable_gzip'), ('.vot', 'votable'), ('.xml', 'votable'), ('.ecsv', 'ecsv'),
                          ('.csv', 'csv'), ('.json', 'json')])
def test_job_get_results(capsys, tmpdir, extension, output_format):
    job = Job(async_job=True)
    jobid = "12345"
    outputFormat = output_format
    job.jobid = jobid
    job.parameters['format'] = outputFormat
    responseCheckPhase = DummyResponse(500)
    responseCheckPhase.set_data(method='GET', body='FINISHED')
    waitRequest = f"async/{jobid}/phase"
    connHandler = DummyConnHandler()
    connHandler.fileExt = extension
    connHandler.set_response(waitRequest, responseCheckPhase)
    job.connHandler = connHandler

    with pytest.raises(Exception):
        job.get_results()

    responseCheckPhase.set_status_code(200)
    responseGetData = DummyResponse(500)
    file_0 = "result_1" + extension
    file = get_pkg_data_filename(os.path.join("data", file_0), package=package)
    if extension in ['.vot.gz']:
        responseGetData.set_data(
            method="GET",
            body=file)
    else:
        responseGetData.set_data(
            method="GET",
            body=Path(file).read_text())
    dataRequest = f"async/{jobid}/results/result"
    connHandler.set_response(dataRequest, responseGetData)

    with pytest.raises(Exception):
        job.get_results()

    responseGetData.set_status_code(200)
    res = job.get_results()
    assert len(res) == 1
    assert len(res.columns) == 2
    for cn in ['solution_id', 'source_id']:
        if cn not in res.colnames:
            pytest.fail(f"{cn} column name not found: {res.colnames}")

    # Increase coverage
    responseGetData.set_status_code(200)
    job.parameters['responseformat'] = outputFormat
    res = job.get_results()
    assert len(res) == 1
    assert len(res.columns) == 2
    for cn in ['solution_id', 'source_id']:
        if cn not in res.colnames:
            pytest.fail(f"{cn} column name not found: {res.colnames}")

    # Regression test for #2299; messages were printed even with `verbose=False`
    capsys.readouterr()
    job._Job__resultInMemory = False
    job.save_results(verbose=False)
    assert 'Saving results to:' not in capsys.readouterr().out
    job.save_results(verbose=True)
    assert 'Saving results to:' in capsys.readouterr().out

    # Increase coverage
    responseGetData.set_status_code(404)
    job._Job__resultInMemory = False
    responseGetData.set_data(method="GET", body="hola")
    error_message = "Error 404:\n.*"
    with pytest.raises(Exception, match=error_message):
        job.save_results(verbose=False)

    for p in Path(".").glob("async_*" + extension):
        p.unlink()


@pytest.mark.parametrize("extension, output_format",
                         [('.vot', 'votable'), ('.xml', 'votable'), ('.ecsv', 'ecsv'), ('.csv', 'csv'),
                          ('.fits', 'fits')])
@pytest.mark.parametrize("verbose", [True, False])
def test_job_save_results(capsys, tmpdir, extension, output_format, verbose):
    job = Job(async_job=True)
    jobid = "12345"
    outputFormat = output_format
    job.jobid = jobid
    job.parameters['format'] = outputFormat
    responseCheckPhase = DummyResponse(500)
    responseCheckPhase.set_data(method='GET', body='FINISHED')
    waitRequest = f"async/{jobid}/phase"
    connHandler = DummyConnHandler()
    connHandler.fileExt = extension
    connHandler.set_response(waitRequest, responseCheckPhase)
    job.connHandler = connHandler

    job.outputFile = 'async_' + extension
    file_0 = "result_1.vot"
    file = get_pkg_data_filename(os.path.join("data", file_0), package=package)
    job.set_results(Table.read(Path(file)))
    job.save_results(verbose=verbose)

    assert Path(job.outputFile).exists() is True

    for p in Path(".").glob("async_*" + extension):
        p.unlink()

    job.set_results(from_table(Table.read(Path(file))))
    job.save_results(verbose=verbose)

    assert Path(job.outputFile).exists() is True

    for p in Path(".").glob("async_*" + extension):
        p.unlink()


def test_job_phase():
    job = Job(async_job=True)
    jobid = "12345"
    outputFormat = "votable"
    job.jobid = jobid
    job.parameters['format'] = outputFormat
    job.set_phase("COMPLETED")
    try:
        job.set_phase("RUN")
        pytest.fail("Exception expected. Phase cannot be changed for a finished job")
    except ValueError:
        # ok
        pass
    try:
        job.start()
        pytest.fail("Exception expected. A job in 'COMPLETE' phase cannot be started")
    except ValueError:
        # ok
        pass
    try:
        job.abort()
        pytest.fail("Exception expected. A job in 'COMPLETE' phase cannot be aborted")
    except ValueError:
        # ok
        pass
