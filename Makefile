test:
	python3 setup.py build_ext -b .
	python3 -m unittest
