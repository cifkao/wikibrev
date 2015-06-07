#!/usr/bin/env python

from distutils.core import setup, Extension
from Cython.Build import cythonize

setup(
        name="wikibrev",
        packages = ['wikibrev'],
        ext_modules = cythonize(Extension(
            "wikibrev._unzim",
            sources=["wikibrev/_unzim.pyx"],
            libraries=["zim", "stdc++"],
            language="c++",
        )),
        scripts=['bin/wikibrev']
)
