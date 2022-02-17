# -*- coding: UTF-8 -*-
"""
This provides a handy image cache for PIL heavy TKInter work.
"""
import os
import shutil
import configparser
import sysconfig
from pathlib import Path
from pickle import dump, load, UnpicklingError
from collections import OrderedDict
from PIL import Image, UnidentifiedImageError, PngImagePlugin
try:
    from ImageTK import ImageTk
except ImportError:
    from .ImageTK import ImageTk


WORKING_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__)))
DEFAULTS = Path(WORKING_DIR + '/default.ini')
pilimg = type(Image)


def config(config_file: Path = DEFAULTS, section: str = 'cache') -> configparser:
    """
    This will grab our settings.
    :return: configparser
    """
    cfg = configparser.ConfigParser()
    cfg.read(config_file)
    cfg = cfg[section]
    settings = dict()
    for setting in list(cfg.keys()):
        try:
            value = eval(cfg[setting])
        except SyntaxError:
            value = cfg[setting]
        settings.update({setting: value})
    return settings


def prep_env(config_file: Path = DEFAULTS, reload: bool = False) -> Path:
    """
    This will get our filesystem setup for saving and transforming resources.
    """
    cfg = config(config_file)
    img_cache = Path(cfg['cache_dir'])
    if reload:
        shutil.rmtree(img_cache)
    dirs = [img_cache, Path(cfg['error_dir'])]
    for dr in dirs:
        dr.mkdir(parents=True, exist_ok=True)
    return img_cache


class Cache:
    """
    This provides the LRU cache logic.
    """
    cache_loaded = False

    def __init__(self, config_file: Path = DEFAULTS):
        self.env = prep_env
        self.dir = self.env(config_file)
        self.cache = OrderedDict()
        self.cache_file = self.dir.stem + '.bin'
        self.config = config(config_file)
        self.capacity = self.config['cache_max']
        self.error_file = Path(str(sysconfig.get_paths()["purelib"]) + '/err.png')

    def trim(self):
        """
        resizes the cache to fit params.
        """
        trim = False
        print('cache size', len(self.cache))  # TODO: Remove after testing.
        if len(self.cache) > self.capacity:
            print('trimming cache')
            trim = True

        while len(self.cache) > self.capacity:
            self.cache.popitem(last=False)

        if trim:
            print('trimmed to', len(self.cache))  # TODO: Remove after testing.

    def get(self, key: [int, str]):
        """
        This fetches items from the cache.
        """
        if key not in self.cache:
            return -1
        else:
            self.cache.move_to_end(key)
            return self.cache[key]

    def put(self, key: [int, str], value) -> None:
        """
        This stores items into the cache.
        """
        self.cache[key] = value
        self.cache.move_to_end(key)
        self.trim()

    def keys(self) -> list:
        """
        Simulates a normal dictionary's keys method.
        """
        return list(self.cache.keys())

    def update(self, kwargs: dict):
        """
        Simulates a normal dictionary's update method.
        """
        for arg in kwargs:
            self.put(arg, kwargs[arg])
        return self

    def save_cache_file(self):
        """
        In the event we are using a cached bin file, this will save / update it.
        """
        print('saving cache bin')
        self.trim()
        with open(self.cache_file, "wb") as cache_file:
            dump(self.cache, cache_file)
            cache_file.close()
        return self

    def load_cache_file(self):
        """
        load the cache file.
        """
        if not self.cache_loaded:
            print('loading cache from bin')
            with open(self.cache_file, 'rb') as cache_file:
                self.cache = load(cache_file)
                cache_file.close()
                del cache_file
                self.cache_loaded = True
        self.trim()
        return self

    def load_image(
            self, file: [open, Image.Image, PngImagePlugin.PngImageFile],
            filename: str,
            passthrough: [dict, None] = None,
    ) -> dict:
        """
        This will load an image file into data and cleanup the file instance.

        Take careful note of the image open, load, update, and close operations used here. If this process is improperly
        altered it will result in significant memory leakage.
        """
        single = False
        name = filename.split('.')[0]
        if not passthrough:
            passthrough = {
                name: {'filename': filename}
            }
            single = True
        if isinstance(file, (pilimg, Image.Image, PngImagePlugin.PngImageFile)):
            im = file
            im.load()
        else:
            try:
                im = Image.open(file)
            except UnidentifiedImageError as err:
                im = Image.open(self.error_file)
                print('RCACHE FAILED TO REFRESH:', err, file)
                if self.config['debug_images']:
                    shutil.copy(self.dir / filename, Path(self.config['error_dir']))
            im.load()
            file.close()
        passthrough[name].update(
            {'body': im}
        )
        del file
        if single:
            self.cache.update(passthrough)
        return passthrough

    def refresh(self, resave: bool = False):
        """
        Refreshes our cache contents.

        param resave: If set to true this will force an update of the saved BIN file.

        """
        if self.config['purge_cache_on_startup'] and os.path.isfile(self.cache_file):  # Debugging.
            os.remove(self.cache_file)
        if os.path.isfile(self.cache_file):
            try:
                self.load_cache_file()
            except (EOFError, UnpicklingError)as err:
                print(err, 'image cache-file damaged, recreating')
                os.remove(self.cache_file)
        else:
            print('loading cache from file system')
        cache = os.listdir(self.dir)
        if len(cache) > 0:
            print('importing new images')
        for item in cache:
            name = item.split('.')[0]
            it = {
                name: {'filename': item}
            }
            if self.config['preload']:
                with open(self.dir / item, 'rb', 0) as f:
                    it = self.load_image(file=f, filename=item, passthrough=it)

            self.cache.update(it)
            if not self.config['debug_images']:
                os.remove(self.dir / item)  # Remove the file before saving it into the bin.
            resave = True
        if resave:
            self.save_cache_file()
        return self
