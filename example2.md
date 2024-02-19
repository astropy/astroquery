---
jupyter:
  jupytext:
    text_representation:
      extension: .md
      format_name: markdown
      format_version: '1.3'
      jupytext_version: 1.16.0
  kernelspec:
    display_name: aquery
    language: python
    name: aquery
---

```python
import os
import sys
from astropy.coordinates import SkyCoord
from astropy import units as u
from astroquery.heasarc import Xamin
from astroquery.heasarc import Heasarc
import astroquery
import warnings
import pyvo
import time
```

```python
Xamin._missions
```

```python
#Xamin._missions
query = ("select distinct split_part(value, ':', 2) "
         "as mission_name from metainfo where value like 'mission:%'")
query = "select top 100 * from metainfo where value lidke 'mission:ans'"
t = Xamin.query_tap(query)
t
```

```python
#Xamin.query_mission_list()
```

```python

```
