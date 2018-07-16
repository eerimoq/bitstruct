test:
	python2 setup.py test
	python3 setup.py test
	$(MAKE) test-sdist
	codespell -d $$(git ls-files)

test-sdist:
	rm -rf dist
	python setup.py sdist
	cd dist && \
	mkdir test && \
	cd test && \
	tar xf ../*.tar.gz && \
	cd bitstruct-* && \
	python setup.py test

release-to-pypi:
	python setup.py sdist
	python setup.py bdist_wheel --universal
	twine upload dist/*
