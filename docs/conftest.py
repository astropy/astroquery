import os
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def tmp_doctest_path(request, tmp_path):
    """Run doctests in isolated temp dir so outputs do not end up in repo"""
    # Trigger ONLY for doctestplus
    doctest_plugin = request.config.pluginmanager.getplugin("doctestplus")
    if isinstance(request.node.parent, doctest_plugin._doctest_textfile_item_cls):
        start_path = Path.cwd()
        os.chdir(tmp_path)
        try:
            yield tmp_path
        finally:
            os.chdir(start_path)
    else:
        yield
