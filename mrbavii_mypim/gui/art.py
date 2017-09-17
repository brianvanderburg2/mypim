""" Art provider class. """

# TODO: make this generic/reusable and move to mrbaviirc

__author__      =   "Brian Allen Vanderburg II"
__copyright__   =   "Copyright (C) 2017 Brian Allen Vanderburg II"
__license__     =   "Apache License 2.0"

import os

import wx

class ArtProvider(wx.ArtProvider):
    def __init__(self, path):
        wx.ArtProvider.__init__(self)
        self._path = path
        self._sizes = {
            16: "16x16",
            32: "32x32",
            48: "48x48",
            64: "64x64",
            128: "128x128",
            256: "256x256"
        }


    def CreateBitmap(self, artid, artclient, size):
        # We don't use the art client, just the artid and size

        sizes = reversed(sorted(self._sizes.keys()))
        best = None

        for i in sizes:
            sizepath = os.path.join(self._path, self._sizes[i])

            filename = os.path.join(sizepath, "{0}.png".format(artid))
            if os.path.isfile(filename):
                if i >= size.width or best is None:
                    best = filename

        if best:
            return wx.BitmapFromImage(wx.Image(best))
        else:
            return wx.NullBitmap



