#!/usr/bin/env python
import os
import platform

import setuptools


def _getenv_bool(key: str) -> bool:
    return os.getenv(key, "false").lower() in ("true", "1")


if platform.python_implementation() == "CPython" and not _getenv_bool("PURE_PYTHON"):
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
