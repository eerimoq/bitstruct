#!/usr/bin/env python

import sys
import setuptools
import platform


def is_cpython_3():
    if platform.python_implementation() != "CPython":
        return False

    if sys.version_info[0] < 3:
        return False

    return True


def setup(ext_modules):
    setuptools.setup(
        ext_modules=ext_modules,
    )


if is_cpython_3():
    try:
        setup(
            [
                setuptools.Extension(
                    "bitstruct.c",
                    sources=["src/bitstruct/c.c", "src/bitstruct/bitstream.c"],
                )
            ]
        )
    except:
        print("WARNING: Failed to build the C extension.")
        setup([])
else:
    print("INFO: C extension only implemented in CPython 3.")
    setup([])
