# -*- coding: UTF-8 -*-
"""
This will put our cache through some simple unit-tests.
"""
import os
import shutil
from pathlib import Path
from PIL import Image, ImageChops
from rcache import Cache


HERE = os.path.abspath(os.path.dirname(__file__))
CACHE = Cache(config_file=Path(HERE + '/config.ini'))
CACHE_BIN = Path(HERE + '/.imgcache.bin')
CACHE_DIR = Path(HERE + '/.imgcache')
ERROR_DIR = Path(HERE + '/rcache_errors')
GOOD = Image.open(Path(HERE + '/good.png'))


def test_structure():
    """
    Confirm the environment is created without issue.
    """
    assert ERROR_DIR.is_dir() and CACHE_DIR.is_dir()


def test_load():
    """
    Copy the test image into the cache dir, load it into memory and save the model to file.
    """
    shutil.copy(Path(HERE + '/good.png'), CACHE_DIR)
    CACHE.refresh(resave=True)
    assert CACHE_BIN.is_file()


def test_get_image():
    """
    Confirm that we can load the image we just saved.
    """
    image_data = CACHE.get('good')
    image = image_data['body']
    diff = ImageChops.difference(image, GOOD)
    assert not diff.getbbox()


def test_clear():
    """
    See if we can clear out the cache properly.
    """
    CACHE.clear(persistent=True)
    assert not len(CACHE.cache.keys()) and not CACHE_BIN.is_file()


def test_cleanup():
    """
    This is a dummy test used to clean up the leftovers.
    """
    shutil.rmtree(ERROR_DIR)
    shutil.rmtree(CACHE_DIR)
    assert True
