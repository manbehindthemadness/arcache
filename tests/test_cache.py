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
CACHE = Cache(config_file=Path(HERE + '/config.ini'), debug=True)
CACHE_BIN = Path(HERE + '/.imgcache.bin')
CACHE_DIR = Path(HERE + '/.imgcache')
ERROR_DIR = Path(HERE + '/rcache_errors')
GOOD = Image.open(Path(HERE + '/good.png'))
ERR = Image.open(Path(HERE + '/err.png'))


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
    shutil.copy(Path(HERE + '/bad.png'), CACHE_DIR)
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


def test_missing_image():
    """
    Confirm that we get a -1 result for a missing image.
    """
    image_data = CACHE.get('missing')
    assert image_data == -1


def test_image_debug():
    """
    Confirms that when image debugging is enabled we save a copy of problematic files into the errors' folder.
    """
    image = Path(ERROR_DIR / 'bad.png')
    assert image.is_file()


def test_unusable_file_substitution():
    """
    This will prove that usable images will be substitutes with the error icon so, they can be easily identified
    on the UX for troubleshooting.
    """
    image_data = CACHE.get('bad')
    image = image_data['body']
    diff = ImageChops.difference(image, ERR)
    assert not diff.getbbox()


def test_lru_functionality():
    """
    This just ensures that we are properly cleaning up images after we hit the maximum configured value.
    """
    os.rename(Path(CACHE_DIR / 'good.png'), Path(CACHE_DIR / 'good_2.png'))
    CACHE.refresh()
    assert len(CACHE.cache.keys()) == 2


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
