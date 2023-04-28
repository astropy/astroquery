# Licensed under a 3-clause BSD style license - see LICENSE.rst
import astropy.units as u
import astropy.coordinates as coord
import astropy.io.votable as votable
import json
import websocket
import time
from astropy.table import Table
from astropy.io import fits

from ....query import BaseQuery
from ....utils import prepend_docstr_nosections
from ....utils import async_to_sync

from . import conf

__all__ = ['SOFIA', 'SOFIAClass']

@async_to_sync
class SOFIAClass(BaseQuery):

    URL = conf.server
    SOFIA_URL = URL + '/applications/sofia'
    TIMEOUT = conf.timeout

    def __init__(self):
        super().__init__()
        self.logged_in = False

    def _login(self):

        resp1 = self._request("GET", self.SOFIA_URL)
        resp1.raise_for_status()

        # "get" sync twice in a row (this is what the web interface does)
        respsync1 = self._request("GET",
                                  f'{self.URL}/frontpage/CmdSrv/sync',
                                  params={'cmd': 'CmdGetUserInfo',
                                          'backToUrl': self.SOFIA_URL}
                                 )
        respsync1.raise_for_status()

        respsync2 = self._request("GET",
                                  f'{self.URL}/frontpage/CmdSrv/sync',
                                  params={'cmd': 'CmdGetUserInfo',
                                          'backToUrl': self.SOFIA_URL}
                                 )
        respsync2.raise_for_status()

        # Connect to websocket - websocket contains informa
        ws = websocket.WebSocket()
        ws.connect('wss://irsa.ipac.caltech.edu/applications/sofia/sticky/firefly/events')

        wsresp = ws.recv()
        message = json.loads(wsresp)
        ws.close() # no longer needed

        # uncertain if we need all of these but I wrote 'em out anyway
        headers = {}
        headers['DNT'] = '1'
        headers['FF-channel'] = message['data']['channel']
        headers['FF-connID'] = message['data']['connID']
        headers['Cache-Control'] = 'no-cache'
        headers['Connection'] = 'keep-alive'
        headers['Host'] = 'irsa.ipac.caltech.edu'
        headers['Origin'] = 'https://irsa.ipac.caltech.edu'
        headers['Pragma'] = 'no-cache'

        # Hopefully don't need this?
        # cookie = {'value': message['data']['channel'],
        #           'domain': 'irsa.ipac.caltech.edu',
        #           'path': '/applications/sofia',
        #           'name': 'usrkey',
        #          }
        # cookie_obj = requests.cookies.create_cookie(**cookie)
        # S.cookies.set_cookie(cookie_obj)
        # S.cookies['ISIS'] = 'TMP_IL5v4i_18662'

        resp1a = self._request('POST',
                               f'{self.SOFIA_URL}/CmdSrv/sync',
                               params={'cmd': 'CmdInitApp'},
                               data={'spaName': '--HydraViewer',
                                     'cmd': 'CmdInitApp'}
                              )
        resp1a.raise_for_status()

        resp2 = self._request('GET', f'{self.SOFIA_URL}/CmdSrv/async')
        resp2.raise_for_status()

        resp3 = self._request('POST', f'{self.URL}/frontpage/CmdSrv/sync',
                              data={'cmd': 'CmdGetUserInfo',
                                    'backToUrl': f'{self.SOFIA_URL}/?__action=layout.showDropDown&'})
        resp3.raise_for_status()


        resp4 = self._request('GET', f'{self.SOFIA_URL}/CmdSrv/async')
        resp4.raise_for_status()

        resp5 = self._request('POST', f'{self.SOFIA_URL}/CmdSrv/sync',
                              params={'cmd': 'pushAction'},
                              data={'channelID': message['data']['channel'],
                                    'action': json.dumps({"type":
                                                          "app_data.notifyRemoteAppReady",
                                                          "payload": {"ready":
                                                                      True,
                                                                      "viewerChannel":
                                                                      message['data']['channel']}}),
                                    'cmd': 'pushAction'})
        resp5.raise_for_status()

        self.logged_in = True


    def query_async(self, *, get_query_payload=False, cache=True):
        """


        Parameters
        ----------
        get_query_payload : bool, optional
            This should default to False. When set to `True` the method
            should return the HTTP request parameters as a dict.
        verbose : bool, optional
           This should default to `False`, when set to `True` it displays
           VOTable warnings.

        Returns
        -------
        response : `requests.Response`
            The HTTP response returned from the service.
            All async methods should return the raw HTTP response.

        Examples
        --------
        While this section is optional you may put in some examples that
        show how to use the method. The examples are written similar to
        standard doctests in python.

        """

        if not self.logged_in:
            self._login()

        request_payload = {
            'request': json.dumps(
                {"startIdx":0,
                 "pageSize":100,
                 "ffSessionId":f"FF-Session-{int(time.time()):d}",
                 "id":"SofiaQuery",
                 "searchtype":"ALLSKY",
                 "proposalSection":"closed",
                 "observationSection":"closed",
                 "instrument":"FORCAST",
                 "configuration":"",
                 "bandpass_name":"",
                 "instrumentSection":"open",
                 "processing":"LEVEL_4,LEVEL_3",
                 "obstype":"",
                 "dataProductSection":"open",
                 #"searchtype":"SINGLE",
                 #"UserTargetWorldPt":"290.9583333333333;14.1;EQ_J2000;w51;simbad",
                 #"radius":"2",
                 "camera":"SW,LW",
                 "META_INFO": {"title": "FORCAST",
                               "tbl_id": "FORCAST",
                               "AnalyzerId": "analyze-sofia",
                               "AnalyzerColumns": "product_type, instrument, processing_level",
                               "DEFAULT_COLOR": "pink",
                               "DataSource": "file_url",
                               "ImagePreview": "preview_url",
                               "selectInfo": "false--0"},
                 "tbl_id":"FORCAST",
                 "spectral_element":"",
                 "tab":"instrument"}),
            'cmd': 'tableSearch'
                   }
        request_payload.update(kwargs)

        if get_query_payload:
            return request_payload

        url = self.URL + '/applications/sofia/CmdSrv/sync'

        response = self._request('POST', url,
                                 params={'cmd': 'tableSearch'},
                                 data=request_payload,
                                 timeout=self.TIMEOUT,
                                 cache=cache)
        return response



SOFIA = SOFIAClass()
