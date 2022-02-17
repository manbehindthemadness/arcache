# -*- coding: UTF-8 -*-
"""
This file is part of the Graphiend application family.
Copyright (c) 2021 Kevin Eales.

This program is experimental and proprietary, redistribution is prohibited.
Please see the license file for more details.
-----------------------------------------------------------------------------------------------------------------------
This is a modified version of PIL.ImageTk, The idea here is to retain the original image so it can be hot-loaded
into cache at the end of the process.
"""

from PIL import PngImagePlugin, Image, ImageTk as ITK
from PIL.ImageTk import PhotoImage as PI

_pilimage = type(Image.Image)


class PhotoImage(PI):
    """
    This is a wrapper class.
    """
    image = None

    def __init__(self, image=None, size=None, **kw):
        PI.__init__(self, image=image, size=size, **kw)
        if image is None:
            image = ImageTk._get_image_from_kw(kw)  # noqa
        if isinstance(image, Image.Image):
            self.image = image
        elif isinstance(image, PngImagePlugin.PngImageFile):
            self.image = image  # This is here in case we need to handle this type a little different.
        else:
            print('foreign image detected', type(image))

    def purge(self):
        """
        Keep our memory clear.
        """
        self.image = None
        return self


ITK.PhotoImage = PhotoImage
ImageTk = ITK
