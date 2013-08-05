all:
	cd ..; \
	git checkout gh-pages; \
	git checkout master -- README.rst; \
	rst2html.py --stylesheet=stylesheets/styles.css,stylesheets/pygment_trac.css,stylesheets/normalize.css,stylesheets/ie.css --link-stylesheet README.rst index.html; \
	rm README.rst; \
	git reset; \
	git add index.html; \
	git commit -m "Index.html generated."; \
	git checkout master; \
	cd -
