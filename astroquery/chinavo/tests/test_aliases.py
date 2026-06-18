# Licensed under a 3-clause BSD style license - see LICENSE.rst

import importlib

import pytest


ALIAS_MODULES = [
    "cstar",
    "fashi",
    "lamost",
    "legacyplate",
    "sage",
    "scuss",
]


def test_chinavo_top_level_aliases_match_nadc():
    nadc_module = importlib.import_module("astroquery.nadc")
    chinavo_module = importlib.import_module("astroquery.chinavo")

    assert sorted(chinavo_module.__all__) == sorted(nadc_module.__all__)
    for public_name in chinavo_module.__all__:
        assert getattr(chinavo_module, public_name) is getattr(nadc_module, public_name)


@pytest.mark.parametrize("module_name", ALIAS_MODULES)
def test_chinavo_package_aliases_match_nadc(module_name):
    nadc_module = importlib.import_module(f"astroquery.nadc.{module_name}")
    chinavo_module = importlib.import_module(f"astroquery.chinavo.{module_name}")

    assert sorted(chinavo_module.__all__) == sorted(nadc_module.__all__)
    for public_name in chinavo_module.__all__:
        assert getattr(chinavo_module, public_name) is getattr(nadc_module, public_name)


@pytest.mark.parametrize("module_name", ALIAS_MODULES)
def test_chinavo_core_aliases_match_nadc(module_name):
    nadc_core = importlib.import_module(f"astroquery.nadc.{module_name}.core")
    chinavo_core = importlib.import_module(f"astroquery.chinavo.{module_name}.core")

    assert sorted(chinavo_core.__all__) == sorted(nadc_core.__all__)
    for public_name in chinavo_core.__all__:
        assert getattr(chinavo_core, public_name) is getattr(nadc_core, public_name)


@pytest.mark.parametrize("module_name", ["_query_data", "_response_utils"])
def test_chinavo_internal_modules_alias_nadc(module_name):
    nadc_module = importlib.import_module(f"astroquery.nadc.{module_name}")
    chinavo_module = importlib.import_module(f"astroquery.chinavo.{module_name}")

    assert chinavo_module is nadc_module
