#!/usr/bin/env python

from setuptools import setup
from setuptools import find_packages
import re


def find_version():
    return re.search(r"^__version__ = '(.*)'$",
                     open('bitstruct/version.py', 'r').read(),
                     re.MULTILINE).group(1)


setup(name='bitstruct',
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
      test_suite="tests")
