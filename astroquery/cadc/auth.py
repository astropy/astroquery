# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
=============
Cadc Auth
=============

"""

import netrc as netrclib
import os
import sys
import getpass

class AuthMethod(object):
    """
    Class to be inherited by all the authentication method classes
    """
    def __init__(self, auth_type):
      self.__authMethod = auth_type

    def get_auth_method(self):
        """
        Returns either 'anon', 'netrc' or 'certificate'
        """
        return self.__authMethod

class CertAuthMethod(AuthMethod):
    """
    Certificate Authentication Method
    """
    def __init__(self, certificate=None):
        """
        Initialize

        Parameter
        certificate : location of file of certificate to use 
                       for authentication
        """       
        super(CertAuthMethod, self).__init__('certificate')
        if certificate is not None:
            assert certificate is not '' and os.path.isfile(certificate),\
                'Certificate file {} not found'.format(certificate)
            self._certificate = certificate
  
    def get_certificate(self):
        """
        Returns the location of the certificate
        """
        return self._certificate

class NetrcAuthMethod(AuthMethod):
    """
    Netrc Authentication Method
    """
    def __init__(self, filename=None, username=None):
        """
        Initialize

        Parameter
        filename : location of the file to use, default is None 
                   which looks in the home directory for a file
                   called '.netrc'
        """
        super(NetrcAuthMethod, self).__init__('netrc')
        self._username=username
        self._hosts_auth = {}
        if username is None:
            hosts = netrclib.netrc(filename).hosts
            self._netrc = os.path.join(os.environ['HOME'], ".netrc")
            for host_name in hosts:
                self._hosts_auth[host_name] = (hosts[host_name][0],
                                               hosts[host_name][2])
        else:
            self._netrc=None

    def get_auth(self, realm):
        """
        Returns a user/password touple for the given realm.

        :param realm: realm for the authentication
        :return: (username, password) touple or None if subject is anonymous
        or password not found.
        """
        if self._netrc is not None:
            if realm in self._hosts_auth:
                return self._hosts_auth[realm]
            else:
                msg = 'No user/password for {}'.format(realm)
                if self.netrc is not False:
                    msg = '{} in {}'.format(msg,
                                            self.netrc if self.netrc
                                            is not True else '$HOME/.netrc')
                return None
        else:
            if realm in self._hosts_auth \
                    and self._username == self._hosts_auth[realm][0]:
                return self._hosts_auth[realm]
            sys.stdout.write("{}@{}\n".format(self._username, realm))
            sys.stdout.flush()
            self._hosts_auth[realm] = (self._username,
                                       getpass.getpass().strip('\n'))
            sys.stdout.write("\n")
            sys.stdout.flush()
            return self._hosts_auth[realm]


class AnonAuthMethod(AuthMethod):
    """
    Anonymous Authentication Method
    """
    def __init__(self):
       """
       Inizialize
       """
       super(AnonAuthMethod, self).__init__('anon')

