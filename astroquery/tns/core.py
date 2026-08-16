# Licensed under a 3-clause BSD style license - see LICENSE.rst

import astropy
from ..query import BaseQuery
from . import conf
from ..utils.class_or_instance import class_or_instance
from collections import OrderedDict
import json

class TnsClass(BaseQuery):

    def __init__(self):
        self._server = conf.server
        self._bot_name = conf.bot_name
        self._bot_id = conf.bot_id
        self._api_key = conf.api_key
        # TODO: add login 
        pass

    def _set_bot_tns_marker(bot_id, bot_name):
        return 'tns_marker{"tns_id": "' + str(bot_id) + '", "type": "bot", "name": "' + bot_name + '"}'

    def query_object(self, *args):
        get_obj = []
        for arg in args:
            get_obj.append(arg)

        search_url = "https://" + self._server + "/api/get/object"
        tns_marker = self._set_bot_tns_marker(self._bot_id, self._bot_name)
        headers = {'User-Agent': tns_marker}
        json_file = OrderedDict(get_obj)
        search_data = {'api-key': self._api_key, 'data':json.dumps(json_file)}
        response = self._request("POST", search_url, headers=headers, data=search_data)
        # TODO: convert the response to what is expected of an astroquery module