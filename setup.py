# -*- coding: UTF-8 -*-
"""
Setup
"""

from setuptools import setup, find_packages

NAME = "RCache"

__version__ = "0.1"
VERSION = __version__


URL = "https://github.com/manbehindthemadness/rcache"
DESCRIPTION = "LRU Cache for TKInter using PIL"
LONG_DESCRIPTION = """Provides in-memory caching in addition to serialized persistent storage"""
LONG_DESCRIPTION += VERSION

PACKAGES = find_packages(include=['rcache', 'rcache.*'])

classifiers = [
    # Get more strings from
    # http://www.python.org/pypi?%3Aaction=list_classifiers
    "License :: OSI Approved :: BSD License",
    "Natural Language :: English",
    "Operating System :: OS Independent",
    "Programming Language :: Python",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3 :: Only",
    "Programming Language :: Python :: 3.6",
    "Programming Language :: Python :: 3.7",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
]

install_requires = [
    "python_version > '3.4'"
]

setup(
    name=NAME,
    version=VERSION,
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/x-rst",
    python_requires=">=3.5",
    classifiers=classifiers,
    keywords="tkinter, pil, cache",
    author="manbehindthemadness",
    url=URL,
    license="BSD",
    packages=PACKAGES,
    install_requires=install_requires,
)
