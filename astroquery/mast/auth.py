# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
MAST Authentication
===================

This file contains functionality related to
authenticating MAST users.
"""

import os
import keyring

from getpass import getpass

from astroquery import log

from ..exceptions import LoginError

from . import conf


__all__ = []


class MastAuth:
    """
    MAST authentication class, handles MAST authentication token.
    """

    def __init__(self, session, token=None):

        self.SESSION_INFO_URL = conf.server + "/whoami"
        self.AUTH_URL = (conf.server.replace("mast", "auth.mast")
                         + "/token?suggested_name=Astroquery&suggested_scope=mast:exclusive_access")

        self.session = session

        if token:
            self.login(token)

    def login(self, token=None, store_token=False, reenter_token=False):
        """
        Log session into the MAST portal.

        Parameters
        ----------
        token : string, optional
            Default is None.
            The token to authenticate the user.
            This can be generated at
            https://ssoportal.stsci.edu/idp/profile/SAML2/Redirect/SSO?execution=e1s1
            If not supplied, it will be prompted for if not in the keyring or set via $MAST_API_TOKEN
        store_token : bool, optional
            Default False.
            If true, MAST token will be stored securely in your keyring.
        reenter_token :  bool, optional
            Default False.
            Asks for the token even if it is already stored in the keyring or $MAST_API_TOKEN environment variable.
            This is the way to overwrite an already stored password on the keyring.
        """

        if token is None and "MAST_API_TOKEN" in os.environ:
            token = os.environ["MAST_API_TOKEN"]

        if token is None:
            token = keyring.get_password("astroquery:mast.stsci.edu.token", "masttoken")

        if token is None or reenter_token:
            info_msg = "If you do not have an API token already, visit the following link to create one: "
            log.info(info_msg + self.AUTH_URL)
            token = getpass("Enter MAST API Token: ")

        # store token if desired
        if store_token:
            keyring.set_password("astroquery:mast.stsci.edu.token", "masttoken", token)

        self.session.headers["Accept"] = "application/json"
        self.session.cookies["mast_token"] = token
        info = self.session_info()

        if not info["anon"]:
            log.info("MAST API token accepted, welcome {}".format(info["attrib"].get("display_name")))
        else:
            raise LoginError("MAST API token invalid!\n To create a new API token"
                             "visit to following link: " + self.AUTH_URL)

        return not info["anon"]

    def logout(self):
        """
        Log out session.
        """
        self.session.cookies.clear_session_cookies()

    def session_info(self, verbose=False):
        """
        Returns user info dictionary and optionally prints info to stdout.

        Parameters
        ----------
        verbose : bool, optional
            Default False. Set to True to print output to stdout.

        Returns
        -------
        response : dict
        """

        # get user information
        self.session.headers["Accept"] = "application/json"
        response = self.session.request("GET", self.SESSION_INFO_URL)

        info = response.json()

        if verbose:
            for key, value in info.items():
                if isinstance(value, dict):
                    for subkey, subval in value.items():
                        print("{}.{}: {}".format(key, subkey, subval))
                else:
                    print("{}: {}".format(key, value))

        return info
