#!/usr/bin/env python
import platform

import setuptools


if platform.python_implementation() in ("CPython", "PyPy"):
    ext_modules = [
        setuptools.Extension(
            "bitstruct.c",
            sources=["src/bitstruct/c.c", "src/bitstruct/bitstream.c"],
        )
    ]

    setuptools.setup(
        ext_modules=ext_modules,
    )
