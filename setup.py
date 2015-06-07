#!/usr/bin/env python

from setuptools import setup, Extension
try:
    from Cython.Build import cythonize
    HAVE_CYTHON = True
except ImportError as e:
    HAVE_CYTHON = False

extensions = [Extension(
    'wikibrev._unzim',
    sources=[
        'wikibrev/_unzim.pyx' if HAVE_CYTHON else 'wikibrev/_unzim.cpp'
    ],
    libraries=['zim', 'stdc++'],
    language='c++'
)]

if HAVE_CYTHON:
    extensions = cythonize(extensions)

setup(
        name='wikibrev',
        version='0.0',
        url='https://github.com/cifkao/wikibrev',
        description='A tool for extracting abbreviations from Wikipedia dumps',
        packages = ['wikibrev'],
        ext_modules = extensions,
        scripts=['bin/wikibrev'],
        install_requires=['filemagic']
)
