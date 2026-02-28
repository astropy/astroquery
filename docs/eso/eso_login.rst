
****************************
Authenticated Access (Login)
****************************

Most datasets in the ESO Science Archive are publicly available and can be downloaded anonymously without requiring authentication. However, access to proprietary datasets—such as those under active proprietary periods—is restricted to authorised users (e.g., PIs of observing programmes and their designated delegates). These users must authenticate via the `ESO User Portal <https://www.eso.org/UserPortal>`_.

Authentication is handled using the :meth:`~astroquery.query.QueryWithLogin.login` method. This command initiates a secure login session via the ESO Single Sign-On (SSO) service. It integrates with the `keyring <https://pypi.org/project/keyring>`_ module to securely store your password in your system’s credential manager. After the first login, you should not need to re-enter your credentials for subsequent sessions on the same machine.

Authentication is required when:

- Downloading proprietary files (not yet public)
- Accessing services that require ESO user privileges

Login Examples
==============

The following examples show typical login and data retrieval workflows:

**First example:** ``"TEST"`` is not a valid username, it will fail:

.. doctest-skip::

    >>> from astroquery.eso import Eso
    >>> eso = Eso()

    >>> eso.login(username="TEST") # doctest: +SKIP
    WARNING: No password was found in the keychain for the provided username. [astroquery.query]
    TEST, enter your password:

    INFO: Authenticating TEST on 'www.eso.org' ... [astroquery.eso.core]
    ERROR: Authentication failed! [astroquery.eso.core]

**Second example:** pretend ``"ICONDOR"`` is a valid username:

.. doctest-skip::

    >>> eso.login(username="ICONDOR", store_password=True) # doctest: +SKIP
    WARNING: No password was found in the keychain for the provided username. [astroquery.query]
    ICONDOR, enter your password:

    INFO: Authenticating ICONDOR on 'www.eso.org' ... [astroquery.eso.core]
    INFO: Authentication successful! [astroquery.eso.core]

After the first login, your password has been stored:

.. doctest-skip::

    >>> eso.login(username="ICONDOR") # doctest: +SKIP
    INFO: Authenticating ICONDOR on 'www.eso.org' ... [astroquery.eso.core]
    INFO: Authentication successful! [astroquery.eso.core]


Successful download of a public file (with or without login):

.. doctest-skip::

    >>> eso.retrieve_data("ADP.2023-03-02T01:01:24.355") # doctest: +SKIP
    INFO: Downloading datasets ... [astroquery.eso.core]
    INFO: Downloading 1 files ... [astroquery.eso.core]
    INFO: Downloading file 1/1 https://dataportal.eso.org/dataPortal/file/ADP.2023-03-02T01:01:24.355 to ... [astroquery.eso.core]
    INFO: Successfully downloaded dataset ADP.2023-03-02T01:01:24.355 to ../ADP.2023-03-02T01:01:24.355.fits [astroquery.eso.core]
    INFO: Done! [astroquery.eso.core]

Access denied to a restricted-access file (as anonymous user or as authenticated but not authorised user):

.. doctest-skip::

    >>> eso.retrieve_data("FORS2.2010-10-23T23:38:41.912") # doctest: +SKIP
    INFO: Downloading datasets ... [astroquery.eso.core]
    INFO: Downloading 1 files ... [astroquery.eso.core]
    INFO: Downloading file 1/1 https://dataportal.eso.org/dataPortal/file/FORS2.2010-10-23T23:38:41.912 to ... [astroquery.eso.core]
    ERROR: Access denied to https://dataportal.eso.org/dataPortal/file/FORS2.2010-10-23T23:38:41.912 [astroquery.eso.core]
    INFO: Done! [astroquery.eso.core]

Password Storage
================

As shown above, your password can be stored securely using the `keyring <https://pypi.org/project/keyring>`_ module by passing the argument ``store_password=True`` to ``Eso.login()``. For security reasons, password storage is disabled by default.

.. warning::

   **MAKE SURE YOU TRUST THE MACHINE WHERE YOU USE THIS FUNCTIONALITY!!!**

   When using the ``store_password=True`` option, your password is stored in your system’s keyring. This provides secure local storage, but only do this on machines you fully trust.

**Note:** You can delete your stored password at any time with the following command:

.. doctest-skip::

    >>> import keyring
    >>> keyring.delete_password("astroquery:www.eso.org", "your_username")

Automatic Login
===============

To avoid having to enter your username every session, you can configure a default username in the Astroquery configuration file. This file is located as described in the `astropy.config documentation <https://docs.astropy.org/en/stable/config/index.html>`_.

Add the following to the ``[eso]`` section of your config file:

.. doctest-skip::

    [eso]
    username = ICONDOR

Once set, you can simply call ``eso.login()`` without specifying a username:

.. doctest-skip::

    >>> eso.login() # doctest: +SKIP
    ICONDOR, enter your ESO password:

**Note:** If automatic login is configured and the password is stored, other ``Eso`` methods (e.g. ``retrieve_data()``) can log you in automatically when needed.
