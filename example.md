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
# # install the astroquery version with the new heasarc updates
# !git clone -b heasarc-xamin --depth 1 https://github.com/zoghbi-a/astroquery.git
# !pip install ./astroquery
```

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
# get all tables
tables = Xamin.tables()
```

```python
tables[:10].pprint(align='<')
```

```python
# list the master tables
master_tables = Xamin.tables(master=True)
```

```python
master_tables.pprint(align='<')
```

```python
# get columns of a single table
cols = Xamin.columns('numaster')
```

```python
# check the first 10 columns
cols[:10]
```

```python
Xamin._get_default_cols('numaster')
```

```python
# search for xmm data on some source
pos = SkyCoord.from_name('ngc 3783')
table = Xamin.query_region(pos, table='xmmmaster')
```

```python
table
```

```python
table['name', 'obsid', 'ra', 'dec'][:3].pprint()
#tab.columns
```

```python
# query circular region around some position
pos = SkyCoord('120 38', unit=u.deg)
tab = Xamin.query_region(pos, table='chanmaster', radius=2*u.deg)
tab['name', 'obsid', 'ra', 'dec'][:5].pprint()
```

```python
# query circular region; choose columns to return
Xamin.query_region(pos, table='xmmmaster', radius=3*u.deg, 
                   columns='obsid, name, time, pi_lname')
```

```python
# query circular region; choose columns to return; 
# generate adql query only
pos = SkyCoord('120 38', unit=u.deg)
query = Xamin.query_region(pos, table='xmmmaster', radius=2*u.deg, get_query_payload=True)
query
```

```python
# Modify the ADQL query and then submit it
query = """SELECT ra,dec,name,obsid FROM xmmmaster 
WHERE CONTAINS(POINT('ICRS',ra,dec),CIRCLE('ICRS',120.0,38.0,2.0))=1"""
tab = Xamin.query_tap(query).to_table()
tab[:10].pprint()
```

```python
# query box region
pos = SkyCoord('226.2 10.6', unit=u.deg)
Xamin.query_region(pos, table='xmmmaster', spatial='box', width=0.5*u.deg)
```

```python
# create the query only for box
pos = SkyCoord('120. 38.0', unit=u.deg)
Xamin.query_region(pos, table='xmmmaster', spatial='box', width=2*u.deg, get_query_payload=True)
```

```python
# query polygon region
Xamin.query_region( table='xmmmaster', spatial='polygon',
                  polygon=[(226.2,10.6),(225.9,10.5),(225.8,10.2),(226.2,10.3)])
```

```python
# a general tap query
query = "SELECT * FROM xmmmaster WHERE 1=CONTAINS(POINT('ICRS', ra, dec), BOX('ICRS', 226.2,10.6,0.5,0.5))"
tab = Xamin.query_tap(query).to_table()
tab[:4].pprint()
```

### Downloading data

```python
# query data
pos = SkyCoord.from_name('ngc 4151')
tab = Xamin.query_region(pos, table='nicermastr')
tab[:4].pprint()
```

```python
# get the links to the data
links = Xamin.get_links(tab[:3])
```

```python
links
```

```python
# Copy data on sciserver: this works only on sciserver
#Xamin.download_data(links[:1], host='sciserver')
```

```python
# download from the heasarc
Xamin.download_data(links[:1], host='heasarc')
```

```python
# download from AWS
Xamin.download_data(links[:1], host='aws')
```

```python

```
