#!/usr/bin/env python

import sys
import re
import setuptools
from setuptools import find_packages


def find_version():
    return re.search(r"^__version__ = '(.*)'$",
                     open('bitstruct/version.py', 'r').read(),
                     re.MULTILINE).group(1)


def setup(ext_modules):
    setuptools.setup(
        name='bitstruct',
        version=find_version(),
        description=('This module performs conversions between Python values '
                     'and C bit field structs represented as Python '
                     'byte strings.'),
        long_description=open('README.rst', 'r').read(),
        author='Erik Moqvist, Ilya Petukhov',
        author_email='erik.moqvist@gmail.com',
        license='MIT',
        classifiers=[
            'License :: OSI Approved :: MIT License',
            'Programming Language :: Python :: 2',
            'Programming Language :: Python :: 3',
        ],
        keywords=['bit field', 'bit parsing', 'bit unpack', 'bit pack'],
        url='https://github.com/eerimoq/bitstruct',
        packages=find_packages(exclude=['tests']),
        ext_modules=ext_modules,
        test_suite="tests")


if sys.version_info[0] > 2:
    try:
        setup([setuptools.Extension('bitstruct.c',
                                    sources=[
                                        'bitstruct/c.c',
                                        'bitstruct/bitstream.c'
                                    ])])
    except:
        print('WARNING: Failed to build the C extension.')
        setup([])
else:
    print('INFO: C extension not implemented in Python 2.')
    setup([])
