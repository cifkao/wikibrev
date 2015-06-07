#!/usr/bin/env python

from setuptools import setup, Extension
from Cython.Build import cythonize

setup(
        name='wikibrev',
        version='0.0',
        url='https://github.com/cifkao/wikibrev',
        description='A tool for extracting abbreviations from Wikipedia dumps',
        packages = ['wikibrev'],
        ext_modules = cythonize(Extension(
            'wikibrev._unzim',
            sources=['wikibrev/_unzim.pyx'],
            libraries=['zim', 'stdc++'],
            language='c++',
        )),
        scripts=['bin/wikibrev'],
        install_requires=['magic']
)
