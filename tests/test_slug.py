# -*- coding: UTF-8 -*-
"""
This will put our slug cache through some simple unit-tests.
"""
import os
import shutil
from pathlib import Path
from PIL import Image
from rcache.ImageTK import ImageTk
from rcache.cache import SlugCache


HERE = os.path.abspath(os.path.dirname(__file__))
CACHE = SlugCache(config_file=Path(HERE + '/config.ini'), debug=True)
ico = Path(HERE + '/round.png')


def icon(file: [str, Path], fill: str, size: int, image: Image = None, raw: bool = False) -> Image:
    """
    This will load a source image as an alpha channel apply it to the color fill and resize to the specified height.
    """
    if not image:
        file = Path(file)
        mask = Image.open(file)
        mask = mask.resize((size, size), resample=Image.ANTIALIAS)
        mask = mask.convert('L')
        image = Image.new("RGB", (size, size), fill)
        image.putalpha(mask)
        if not raw:
            image = ImageTk.PhotoImage(image)
    return image


def kwarg_slugging(image: [Image, None] = None):
    """
    This will take the icon creation function above and use it as a sluggable callback into our cache,
    """
    kwargs = {
        'file': 'round.png',
        'fill': 'green',
        'size': 100,
        'image': image,
        'raw': True
    }
    return CACHE.provide(icon, *[], **kwargs)


def test_open():
    """
    This will call the kwarg slugging function to open our test image, then confirm that we can display the resulting
    composite, and then confirm that we are loading that composite from the file system.
    """
    image = kwarg_slugging()  # noqa
    image.show()
    assert not CACHE.from_memory


def test_slug():
    """
    Confirm that our diagnostic image exists and is properly named.
    """
    assert Path(HERE + '/.imgcache/icon-file-roundptpng-fill-green-size-100-image-none-raw-true.png').is_file()


def test_fetch_from_slug():
    """
    This will re-open the test file and confirm that the kwargs are being evaluated correctly.
    """
    kwarg_slugging()  # noqa
    assert CACHE.from_memory


def test_cleanup():
    """
    Dummy test to clean up the leftovers.
    """
    cache = CACHE
    cache = cache  # Debug hook  noqa
    cache.clear(persistent=True)
    shutil.rmtree(Path(HERE + '/.imgcache'))
    shutil.rmtree(Path(HERE + '/rcache_errors'))
    assert True
