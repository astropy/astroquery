.. doctest-skip-all

Astroquery Testing
==================

Testing in astroquery is a bit more complicated than in other modules since we
depend on remote servers to supply data.  In order to keep the tests green and
fast, we use monkeypatching to test most functions on local copies of the data.

In order to set up testing for any given module, you therefore need to have
local copies of the data.

The testing directory structure should look like::

    module/tests/__init__.py
    module/tests/test_module.py
    module/tests/test_module_remote.py
    module/tests/setup_package.py
    module/tests/data/
    module/tests/data/test_data.xml

``test_module.py``
------------------

This file should contain only tests that do not require an internet connection.
It also contains the tricky monkeypatching components.  At a minimum, monkeypatching
requires a few methods that are defined locally in the test file for each module.

Monkeypatching
~~~~~~~~~~~~~~
At a minimum, monkeypatching will require these changes:

.. code-block:: python

    class MockResponse(object):

        def __init__(self, content):
            self.content = content

``MockResponse`` is an object intended to have any of the attributes that a
normal `requests.Response` object would have.  However, it only needs to
implement the methods that are actually used within the tests.

The tricky bits are in the ``pytest.fixture``.

The first little magical function is the ``patch_x`` function, where ``x`` should
either be ``post`` or ``get``.

.. code-block:: python

    @pytest.fixture
    def patch_get(request):
        mp = request.getfuncargvalue("monkeypatch")
        mp.setattr(requests, 'get', get_mockreturn)
        return mp

This function, when called, changes the `requests.get` method (i.e., the ``get``
method of the ``requests`` module) to call the ``get_mockreturn`` function, defined
below.  ``@pytest.fixture`` means that, if any function in this ``test_module.py``
file accepts ``patch_get`` as an argument, ``patch_get`` will be called prior to
running that function.

``get_mockreturn`` is simple but important: this is where you define a function
to return the appropriate data stored in the ``data/`` directory as a readable
object within the ``MockResponse`` class:

.. code-block:: python

    def get_mockreturn(url, params=None, timeout=10):
        filename = data_path(DATA_FILES['votable'])
        content = open(filename, 'r').read()
        return MockResponse(content)

``data_path`` is a simple function that looks for the ``data`` directory local to
the ``test_module.py`` file.

.. code-block:: python

    def data_path(filename):
        data_dir = os.path.join(os.path.dirname(__file__), 'data')
        return os.path.join(data_dir, filename)

``test_module_remote.py``
-------------------------

The remote tests are much easier.  Just decorate the test class or test
functions with ``astropy.tests.helper.remote_data``.

``setup_package.py``
--------------------

This file only needs the ``get_package_data()`` function, which will tell
``setup.py`` to include the relevant files when installing.

.. code-block:: python

    import os

    def get_package_data():
        paths_test = [os.path.join('data', '*.xml')]

        return {'astroquery.module.tests': paths_test}
