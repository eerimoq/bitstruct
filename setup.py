#!/usr/bin/env python
import platform

import setuptools

if platform.python_implementation() == "CPython":
    ext_modules = [
        setuptools.Extension(
            "bitstruct.c",
            sources=[
                "src/bitstruct/c.c",
                "src/bitstruct/bitstream.c",
            ],
        )
    ]
else:
    ext_modules = []

setuptools.setup(
    ext_modules=ext_modules,
)
