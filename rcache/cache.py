# -*- coding: UTF-8 -*-
"""
This provides a handy image cache for PIL heavy TKInter work.
"""
import os
import re
import shutil
import configparser
import unicodedata
import logging  # noqa
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
    TODO: We should move this into our larger config parser deal at a later time.
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


def clean_args(args: list, kwargs: dict, exclusive: bool = False) -> dict:
    """
    Removes keys to prevent errors.
    """
    kargs = list(kwargs.keys())
    if exclusive:
        for arg in kargs:
            if arg not in args:
                del kwargs[arg]
    else:
        for arg in args:
            try:
                del kwargs[arg]
            except KeyError:
                pass
    return kwargs


def get_args(args: list, kwargs: dict, clean: bool = False) -> list:
    """
    This will fetch arguments and jazz.
    """
    values = list()
    for arg in args:
        if arg in kwargs:
            values.append(kwargs[arg])
        else:
            values.append(None)
    if clean:
        clean_args(args, kwargs)
    if len(values) == 1:
        values = values[0]
    return values


def slugify(value, allow_unicode=False):
    """
    Taken from https://github.com/django/django/blob/master/django/utils/text.py
    Convert to ASCII if 'allow_unicode' is False. Convert spaces or repeated
    dashes to single dashes. Remove characters that aren't alphanumerics,
    underscores, or hyphens. Convert to lowercase. Also strip leading and
    trailing whitespace, dashes, and underscores.
    """
    value = str(value).replace('-', 'ng').replace('.', 'pt')
    if allow_unicode:
        value = unicodedata.normalize('NFKC', value)
    else:
        value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^\w\s-]', '', value.lower())
    return re.sub(r'[-\s]+', '-', value).strip('-_')


def get_name(args: [list, tuple, dict]) -> str:
    """
    This created a name based on passed arguments (handy for caching by config).
    """
    name = slugify(args)
    return name


class Cache:
    """
    This provides the LRU cache logic.
    """
    cache_loaded = False

    def __init__(self, config_file: Path = DEFAULTS, debug: bool = False):
        self.env = prep_env
        self.dir = self.env(config_file)
        self.cache = OrderedDict()
        self.cache_file = self.dir.stem + '.bin'
        self.config = config(config_file)
        self.capacity = self.config['cache_max']
        self.error_file = Path(os.path.abspath(os.path.dirname(__file__)) + '/err.png')
        self.debug = debug
        self.refresh()

    def log(self, *args, **kwargs):
        """
        Really simple-ass logger.
        """
        message = str()
        for arg in args:
            message += str(arg) + ' '
        level = get_args(
            ['level'],
            kwargs
        )
        if not level:
            level = 'info'
        cmd = 'logging.' + level + '(message)'
        exec(cmd)
        return self

    def trim(self):
        """
        resizes the cache to fit params.
        """
        trim = False
        self.log('cache size', len(self.cache))
        if len(self.cache) > self.capacity:
            self.log('trimming cache')
            trim = True

        while len(self.cache) > self.capacity:
            self.cache.popitem(last=False)

        if trim:
            self.log('trimmed to', len(self.cache))

    def get(self, key: [int, str]) -> [int, dict]:
        """
        This fetches items from the cache.
        """
        if key not in self.cache:
            return -1
        else:
            self.cache.move_to_end(key)
            return self.cache[key]

    def put(self, key: [int, str], value):
        """
        This stores items into the cache.
        """
        self.cache[key] = value
        self.cache.move_to_end(key)
        self.trim()
        return self

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
        self.log('saving cache bin')
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
            self.log('loading cache from bin')
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
                self.log('RCACHE FAILED TO REFRESH:', err, file)
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
        if not Path(self.cache_file).is_file():
            self.save_cache_file()
        return passthrough

    def refresh(self, resave: bool = False):
        """
        Refreshes our cache contents.

        param resave: If set to true this will force an update of the saved BIN file.

        """
        if self.config['purge_cache_on_startup'] and os.path.isfile(self.cache_file):  # Debugging.
            os.remove(self.cache_file)
        if Path(self.cache_file).is_file():
            try:
                self.load_cache_file()
            except (EOFError, UnpicklingError)as err:
                self.log(err, 'image cache-file damaged, recreating')
                os.remove(self.cache_file)
        else:
            self.log('loading cache from file system')
        cache = os.listdir(self.dir)
        if len(cache) > 0:
            self.log('importing new images')
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

    def clear(self, persistent: bool = False):
        """
        This allows us to clear the cache contents,
        if persistent is set to True the saved cache file will also be removed.
        """
        self.cache = OrderedDict()
        if persistent:
            if Path(self.cache_file).is_file():
                os.remove(self.cache_file)
        return self


class SlugCache(Cache):
    """
    This will allow us to store and update our images to reduce cpu overhead.
    """
    from_memory = False  # This is used as signal for unit testing.

    def __init__(self, config_file: Path = DEFAULTS, debug: bool = False):
        Cache.__init__(self, config_file, debug)
        self.log('searching for cache file')
        self.temp = dict()

    def save_image(self, image: [ImageTk.PhotoImage, Image.Image], filename: str):
        """
        This will either save the image to file or directly into cache.
        """
        if self.config['debug_images']:
            if isinstance(image, Image.Image):
                image.save(self.dir / filename, "PNG")
            else:
                image._PhotoImage__photo.write(self.dir / filename)  # noqa
        else:
            self.cache.load_image(file=image.image, filename=filename)  # noqa
        return self

    def provide(self, callback, *args, **kwargs) -> Image:
        """
        This will check to see if the callback output is already in the cache and if so return it,
            Otherwise the callback will be executed, the results returned, and then cached.
        """
        if 'exclude' in kwargs.keys():
            exclusions = kwargs['exclude']
            exclusions.append('exclude')
            kwargs = clean_args(
                exclusions,
                kwargs
            )
        raw, no_cache = get_args(
            ['raw', 'no_cache'],
            kwargs
        )
        item = get_name((callback.__name__, args, kwargs))
        filename = item + '.png'  # TODO: We might want to make the file extensions configurable in the future.
        save = True
        if item in self.cache.keys() and not no_cache:
            filename = self.cache.get(item)['filename']
            if 'body' in self.cache.get(item).keys():
                self.log('loading image from memory')
                self.from_memory = True
                image = self.cache.get(item)['body']  # Load from memory.
                image.load()  # Load image into memory and close.
            else:
                self.log('loading image from file')
                self.from_memory = False
                image = Image.open(self.dir / filename)  # Load from file.
                image.load()  # Load image into memory and close.
                self.cache.get(item)['body'] = image  # Save to memory if not present.
            kwargs['image'] = image
            save = False
        image = callback(*args, **kwargs)
        if image and isinstance(image, ImageTk.PhotoImage) and save and not no_cache:
            if 0 not in [image.width(), image.height()]:
                self.save_image(image, filename)
                save = False
            else:
                self.log('zero dimension found in', filename)
        if not isinstance(image, ImageTk.PhotoImage) and not raw and image:
            image = ImageTk.PhotoImage(image)
        if save and image:
            self.save_image(image, filename)
            if not os.path.isfile(self.cache_file):
                self.refresh(resave=True)
        return image
