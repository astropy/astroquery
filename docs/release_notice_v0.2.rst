Astroquery v0.2 has been released.  Astroquery is a suite of tools for querying
various astronomical web forms, including observation archives, source
catalogs, and spectral line lists.

You can access astroquery at
https://pypi.python.org/pypi/astroquery/0.2
or directly from github:
https://github.com/astropy/astroquery/releases/tag/v0.2

The documents are hosted at:
http://astroquery.readthedocs.io/en/v0.2/


v0.2 has a few new features and includes major internal improvements.

The new tools provide interfaces to the ESO Archive, the GAMA database, the CDS
Xmatch service, NASA's SkyView service, and the Open Exoplanet Catalogue.

Thanks to the many contributors this cycle:
Julien Woillez (@jwoillez)
Simon Liedtke (@derdon)
Loïc Séguin-Charbonneau (@loicseguin)
Caden Armstrong (@CadenArmstrong)
Joseph Booker (@sargas)
Erik Tollerud (@eteq)
Madhura Parikh (@jdnc)
@fred3m
Ricky Egeland (@rickyegeland)
Michel Droettboom (@mdboom)
James Allen(@james-allen)
Brigita Sipocz (@bsipocz)
Gustavo Braganca (@gabraganca)
Adrian Price-Whelan (@adrn)
David Shiga (@dshiga)
Matt Craig (@mwcraig)
Kyle Willett (@willettk)
Erik Bray (@embray)
William Schoenell (@wschoenell)
Austen Groener (@agroener)

Astroquery has 30 contributors, about 1/3 that of astropy, making it the
largest affiliated package by contributor count.

This release also coincides with the completion of the GSoC program.  Simon
Liedtke was our student this summer.  He changed astroquery from using lxml to
BeautifulSoup, especially in the ESO package. He also added support for the
services xMatch, SkyView and Atomic Line List.  Documentation has been added
for the packages xmatch and atomic (though note that extensive documentation
exists in form of docstrings for all packages he added, including SkyView). All
new services have tests that can be run both off- and online.

--
Adam Ginsburg, Christoph Deil, and Thomas Robitaille
