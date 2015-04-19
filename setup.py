#!/usr/bin/env python

from distutils.core import setup, Extension
from Cython.Build import cythonize

setup(
        name="unzim",
        py_modules = ['unzim'],
        ext_modules = cythonize(Extension(
            "_unzim",
            sources=["_unzim.pyx"],
            libraries=["zim", "stdc++"],
            language="c++",
)))

