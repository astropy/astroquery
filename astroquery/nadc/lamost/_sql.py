# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""SQL for the structured queries whose archive endpoints lose matches."""


# These configurations lack the OpenAPI /tables endpoint. Do not infer this
# capability from an HTTP failure: authentication and service failures matter.
LEGACY_METADATA = {
    'dr1': ('', 'v2.0'), 'dr2': ('', 'v2.0'), 'dr3': ('', 'v2.0'),
    'dr4': ('v1', 'v2'), 'dr5': ('v0', 'v1', 'v2', 'v3'),
    'dr6': ('v0', 'v1', 'v1.1', 'v2'),
    'dr7': ('v0', 'v1', 'v1.1', 'v1.2', 'v1.3', 'v2.0'),
    'dr8': ('v0', 'v1.0', 'v1.1', 'v2.0'),
    'dr9': ('v0', 'v1.0', 'v1.1', 'v2.0'),
    'dr10': ('v0', 'v1.0'), 'dr11': ('v0',),
}


def uses_legacy_metadata(release, version):
    return version in LEGACY_METADATA.get(release, ())
