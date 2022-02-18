# -*- coding: UTF-8 -*-
"""
Setup
"""

import sys
import os
from setuptools import setup, find_packages

NAME = "rcache"

__version__ = "0.1"
VERSION = __version__


here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.md')) as f:
    README = f.read()


URL = "https://github.com/manbehindthemadness/rcache"
DESCRIPTION = "LRU Cache for TKInter using PIL"
LONG_DESCRIPTION = """Provides in-memory caching in addition to serialized persistent storage"""

PACKAGES = find_packages()

if sys.version_info < (3, 5):
    sys.exit('Sorry, Python < 3.5 is not supported')

install_requires = [
    "Pillow >= 8"
]

setup(
    name=NAME,
    version=VERSION,
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/x-rst",
    keywords="tkinter, pil, cache",
    author="manbehindthemadness",
    author_email="manbehindthemadness@gmail.com",
    url=URL,
    license="MIT",
    packages=PACKAGES,
    install_requires=install_requires,
    package_dir={'': 'src'},
    py_modules=['rcache']
)
