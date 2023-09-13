# -*- coding: utf-8 -*-
# Licensed under a 3-clause BSD style license - see LICENSE.rst

import re
import json
import astropy.utils.data as aud


def reload_votable_fields_json():
    content = aud.get_file_contents("https://simbad.cds.unistra.fr/guide/sim-fscript.htx#VotableFields")

    import bs4
    htmldoc = bs4.BeautifulSoup(content, 'html5lib')
    search_text = re.compile(r'Field names for VOTable output', re.IGNORECASE)
    foundtext = htmldoc.find('h2', text=search_text)

    # Find the first <table> tag that follows it
    table = foundtext.findNext('table')
    outd = {}
    for row in table.findAll('tr'):
        cols = row.findChildren('td')
        if len(cols) > 1:
            smallest_child = cols[0].find_all()[-1]
            if cols[0].findChild("ul"):
                text1 = cols[0].findChild('ul').getText()
            elif cols[0].find_all():
                text1 = smallest_child.getText()
            else:
                text1 = cols[0].getText()
            if cols[1].findChild("ul"):
                text2 = cols[1].findChild('ul').getText()
            else:
                text2 = cols[1].getText()
            # ignore blank entries & headers
            if (text2.strip() != ''
                and not (smallest_child.name == 'font' and 'size' in smallest_child.attrs
                         and smallest_child.attrs['size'] == '+2')):
                outd[text1.strip()] = text2.strip()

    with open('data/votable_fields_dict.json', 'w') as f:
        json.dump(outd, f, indent=2, sort_keys=True)
