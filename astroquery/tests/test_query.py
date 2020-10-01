import os
import pytest
from unittest import mock
import tempfile
import requests
from datetime import datetime
import email.utils as eut

from astroquery import query


def test_download():
    bq = query.BaseQuery()

    get_response = mock.Mock()
    buffer1 = b'This is ..'
    buffer2 = b' just a test'
    get_response.iter_content.return_value = iter([buffer1, buffer2])
    get_response.headers = {'content-length': len(buffer1) + len(buffer2)}

    bq._session = mock.Mock()
    bq._session.request.return_value = get_response
    dest_dir = tempfile.TemporaryDirectory()
    filename = 'test.txt'
    bq._request('GET', 'https://some.url/{}'.format(filename), save=True,
                savedir=dest_dir.name)
    assert open(os.path.join(dest_dir.name, filename), 'r').read() == \
        buffer1.decode('utf-8') + buffer2.decode('utf-8')

    get_response.reset_mock()
    get_response.iter_content.return_value = iter([buffer1, buffer2])
    get_response.headers = {'content-length': len(buffer1) + len(buffer2) + 1}

    with pytest.raises(RuntimeError) as e:
        bq._request('GET', 'https://some.url/{}'.format(filename), save=True,
                    savedir=dest_dir.name)
    assert 'Received incomplete' in str(e)

    get_response.reset_mock()
    get_response.iter_content.return_value = iter([buffer1, buffer2])
    get_response.headers = {'content-length': len(buffer1) + len(buffer2) - 1}

    with pytest.raises(RuntimeError) as e:
        bq._request('GET', 'https://some.url/{}'.format(filename), save=True,
                    savedir=dest_dir.name)
    assert 'Received extra' in str(e)


def test_stale():
    # get a copy of the file first
    bq = query.BaseQuery()
    utcnow = datetime.utcnow()
    get_response = mock.Mock()
    get_response.headers = []
    dest_dir = tempfile.TemporaryDirectory()
    filename = 'test.txt'
    file = os.path.join(dest_dir.name, filename)
    buffer1 = b'This is ..'
    buffer2 = b' just a test1'

    # response contains no size or date headers. Local file is updated
    # every single time
    bq._session = mock.Mock()
    bq._session.request.return_value = get_response
    get_response.iter_content.return_value = iter([buffer1, buffer2])
    bq._request('GET', 'https://some.url/{}'.format(filename), save=True,
                savedir=dest_dir.name)
    assert os.path.isfile(file)
    get_response.iter_content.assert_called()
    assert buffer2.decode('utf-8') in open(file).read()

    # second call. To make sure file is updated, just modify a character
    # so size stays the same
    get_response.iter_content.reset_mock()
    buffer2 = b' just a test2'
    get_response.iter_content.return_value = iter([buffer1, buffer2])
    bq._request('GET', 'https://some.url/{}'.format(filename), save=True,
                savedir=dest_dir.name)
    assert os.path.isfile(file)
    get_response.iter_content.assert_called()
    assert buffer2.decode('utf-8') in open(file).read()

    # Introduce content length header. Sizes are the same but there is no
    # date info so a download occurs
    get_response.iter_content.reset_mock()
    buffer2 = b' just a test3'
    get_response.headers = {'content-length': len(buffer1) + len(buffer2)}
    get_response.iter_content.return_value = iter([buffer1, buffer2])
    bq._request('GET', 'https://some.url/{}'.format(filename), save=True,
                savedir=dest_dir.name)
    assert os.path.isfile(file)
    assert buffer2.decode('utf-8') in open(file).read()
    get_response.iter_content.assert_called()

    # Local copy is considered stalled because there's no Date header
    get_response.iter_content.reset_mock()
    buffer2 = b' just a test4'
    get_response.iter_content.return_value = iter([buffer1, buffer2])
    bq._request('GET', 'https://some.url/{}'.format(filename), save=True,
                savedir=dest_dir.name)
    assert os.path.isfile(file)
    assert buffer2.decode('utf-8') in open(file).read()
    get_response.iter_content.assert_called()

    # Local copy is considered stalled because the file timestamp
    # is too close to the original.
    get_response.iter_content.reset_mock()
    get_response.headers['Date'] = eut.format_datetime(utcnow)
    buffer2 = b' just a test5'
    get_response.iter_content.return_value = iter([buffer1, buffer2])
    bq._request('GET', 'https://some.url/{}'.format(filename), save=True,
                savedir=dest_dir.name)
    assert os.path.isfile(file)
    assert buffer2.decode('utf-8') in open(file).read()
    get_response.iter_content.assert_called()

    # Local copy is considered up-to-date because Date is in the past
    get_response.iter_content.reset_mock()
    get_response.headers['Date'] = 'Tue, 29 Sep 2020 17:00:00 GMT'
    buffer2 = b' just a test6'
    get_response.iter_content.return_value = iter([buffer1, buffer2])
    bq._request('GET', 'https://some.url/{}'.format(filename), save=True,
                savedir=dest_dir.name)
    assert os.path.isfile(file)
    assert buffer2.decode('utf-8') not in open(file).read()
    assert 'test5' in open(file).read()
    get_response.iter_content.assert_not_called()

    # Update size now which should trigger an update
    get_response.iter_content.reset_mock()
    buffer2 = b' just another test'
    get_response.iter_content.return_value = iter([buffer1, buffer2])
    get_response.headers = {'content-length': len(buffer1) + len(buffer2)}
    bq._request('GET', 'https://some.url/{}'.format(filename), save=True,
                savedir=dest_dir.name)
    assert os.path.isfile(file)
    assert buffer2.decode('utf-8') in open(file).read()
    get_response.iter_content.assert_called()
    assert os.stat(file).st_size == get_response.headers['content-length']


@mock.patch('astroquery.query.time.sleep')
@mock.patch('astroquery.query.requests.Session.send')
@mock.patch('astroquery.query.requests.Session.merge_environment_settings',
       mock.Mock(return_value={}))
def test_retry(send_mock, time_mock):
    request = mock.Mock()
    send_mock.return_value = mock.Mock()
    rs = query.RetrySession(False)
    rs.send(request)
    send_mock.assert_called_with(request, timeout=120)

    # retry to user defined timeout
    send_mock.return_value = mock.Mock()
    rs = query.RetrySession(False)
    rs.send(request, timeout=77)
    send_mock.assert_called_with(request, timeout=77)

    # mock delays for the 'Connection reset by peer error'
    # one connection error delay = DEFAULT_RETRY_DELAY
    send_mock.reset_mock()
    rs = query.RetrySession()
    # HTTP error that triggers retries
    transient_response = requests.Response()
    transient_response.status_code = requests.codes.unavailable
    response = requests.Response()
    response.status_code = requests.codes.ok
    send_mock.side_effect = [transient_response, response]
    rs.send(request)
    time_mock.assert_called_with(query.DEFAULT_RETRY_DELAY)

    # two connection error delay = DEFAULT_RETRY_DELAY
    send_mock.reset_mock()
    time_mock.reset_mock()
    rs = query.RetrySession()
    # connection error that triggers retries
    send_mock.side_effect = [transient_response,
                             transient_response,
                             response]  # two connection errors
    rs.send(request)
    calls = [mock.call(query.DEFAULT_RETRY_DELAY),
             mock.call(query.DEFAULT_RETRY_DELAY * 2)]
    time_mock.assert_has_calls(calls)

    # set the start retry to a large number and see how it is capped
    # to MAX_RETRY_DELAY
    send_mock.reset_mock()
    time_mock.reset_mock()
    rs = query.RetrySession(start_delay=query.MAX_RETRY_DELAY / 2 + 1)
    # connection error that triggers retries
    send_mock.side_effect = [transient_response,
                             transient_response,
                             response]  # two connection errors
    rs.send(request)
    calls = (mock.call(query.MAX_RETRY_DELAY / 2 + 1),
             mock.call(query.MAX_RETRY_DELAY))
    time_mock.assert_has_calls(calls)

    # return the error all the time
    send_mock.reset_mock()
    time_mock.reset_mock()
    rs = query.RetrySession(start_delay=query.MAX_RETRY_DELAY / 2 + 1)
    # connection error that triggers retries
    # make sure the mock returns more errors than the maximum number
    # of retries allowed
    http_errors = []
    i = 0
    while i <= query.MAX_NUM_RETRIES:
        http_errors.append(transient_response)
        i += 1
    send_mock.side_effect = http_errors
    with pytest.raises(requests.exceptions.HTTPError) as e:
        rs.send(request)
    assert '503 Server Error' in str(e)

    # return the connection error 104 - connection reset by peer
    send_mock.reset_mock()
    time_mock.reset_mock()
    rs = query.RetrySession(start_delay=query.MAX_RETRY_DELAY / 2 + 1)
    ce = requests.exceptions.ConnectionError()
    ce.errno = 104
    send_mock.side_effect = ce
    with pytest.raises(requests.exceptions.ConnectionError):
        rs.send(request)

    # return HttpError 503 with Retry-After
    send_mock.reset_mock()
    time_mock.reset_mock()
    rs = query.RetrySession()
    server_delay = 5
    # connection error that triggers retries
    he = requests.exceptions.HTTPError()
    he.response = requests.Response()
    he.response.status_code = requests.codes.unavailable
    he.response.headers[query.SERVICE_RETRY] = server_delay
    response = requests.Response()
    response.status_code = requests.codes.ok
    send_mock.side_effect = [he, response]
    rs.send(request)
    calls = [mock.call(server_delay)]
    time_mock.assert_has_calls(calls)

    # return HttpError 503 with Retry-After with an invalid value
    send_mock.reset_mock()
    time_mock.reset_mock()
    start_delay = 66
    rs = query.RetrySession(start_delay=start_delay)
    server_delay = 'notnumber'
    # connection error that triggers retries
    he = requests.exceptions.HTTPError()
    he.response = requests.Response()
    he.response.status_code = requests.codes.unavailable
    he.response.headers[query.SERVICE_RETRY] = server_delay
    response = requests.Response()
    response.status_code = requests.codes.ok
    send_mock.side_effect = [he, response]
    rs.send(request)
    calls = [mock.call(start_delay)]  # uses the default delay
    time_mock.assert_has_calls(calls)

    # return HttpError 503 with no Retry-After
    send_mock.reset_mock()
    time_mock.reset_mock()
    start_delay = 66
    rs = query.RetrySession(start_delay=start_delay)
    he = requests.exceptions.HTTPError()
    he.response = requests.Response()
    he.response.status_code = requests.codes.unavailable
    response = requests.Response()
    response.status_code = requests.codes.ok
    send_mock.side_effect = [he, response]
    rs.send(request)
    calls = [mock.call(start_delay)]  # uses the default delay
    time_mock.assert_has_calls(calls)

    # tests non-transient errors
    send_mock.reset_mock()
    time_mock.reset_mock()
    rs = query.RetrySession()
    he = requests.exceptions.HTTPError()
    he.response = requests.Response()
    he.response.status_code = requests.codes.internal_server_error
    send_mock.side_effect = he
    with pytest.raises(requests.exceptions.HTTPError):
        rs.send(request)
