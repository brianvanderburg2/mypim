""" Art provider class. """

# TODO: make this generic/reusable and move to mrbaviirc

__author__      =   "Brian Allen Vanderburg II"
__copyright__   =   "Copyright (C) 2017 Brian Allen Vanderburg II"
__license__     =   "Apache License 2.0"

import os

from collections import OrderedDict

import wx

class ArtProvider(wx.ArtProvider):
    def __init__(self, path):
        wx.ArtProvider.__init__(self)
        self._default = None

        # Learn our paths
        try:
            subdirs = os.listdir(path)
        except (IOError, OSError) as e:
            subdirs = []
        
        widths = {}
        heights = {}
        for subdir in subdirs:
            # Ignore starting with "."
            if subdir[0:1] == ".":
                continue

            # Dirs only
            fullpath = os.path.join(path, subdir)
            if not os.path.isdir(fullpath):
                continue

            # Is it our default dir
            if subdir == "default":
                self._default = fullpath
                continue

            # Only support WxH
            parts = subdir.split("x")
            if len(parts) != 2:
                continue

            try:
                (width, height) = (int(parts[0]), int(parts[1]))
            except ValueError:
                continue

            if width < 1 or height < 1:
                continue

            # We now have our width and height
            if not width in widths:
                widths[width] = {}
            widths[width][height] = fullpath


        # Now we want to sort them
        self._sizes = OrderedDict()
        for width in sorted(widths.keys()):
            self._sizes[width] = OrderedDict()
            for height in sorted(widths[width].keys()):
                self._sizes[width][height] = widths[width][height]


    def _find_file(self, filename, width, height):
        # Do we have an exact match
        if width in self._sizes and height in self._sizes[width]:
            path = self._sizes[width][height]
            fullpath = os.path.join(path, filename)

            if os.path.isfile(fullpath):
                return fullpath

        # Find best aspect ratios
        closest_aspect = None
        target_aspect = float(width) / float(height)

        for _width in self._sizes:
            for _height in self._sizes[_width]:

                path = self._sizes[_width][_height]
                fullpath = os.path.join(path, filename)

                if not os.path.isfile(fullpath):
                    continue

                our_aspect = float(_width) / float(height)
                diff = abs(target_aspect - our_aspect)

                if diff < 0.01 and _width >= width:
                    # If the aspect is the same, return the first larger or equal image
                    return fullpath

                if closest_aspect is None or diff < closest_aspect[0]:
                    # First found or found a closer aspect ratio
                    closest_aspect = (diff, fullpath, _width)
                elif abs(diff - closest_aspect[0]) < 0.0001 and closest_aspect[2] < width:
                    # Found an equal aspect ratio to the last found one (but
                    # maybe not equal to target), and last image was smaller than
                    # target so prefer this image
                    closest_aspect = (diff, fullpath, _width)
                    
        if closest_aspect:
            return closest_aspect[1]

        if self._default:
            fullpath = os.path.join(self._default, filename)

            if os.path.isfile(fullpath):
                return fullpath

        return None


    def CreateBitmap(self, artid, artclient, size):
        # We don't use the art client, just the artid and size
        filename = str(artid) + ".png"
        fullpath = self._find_file(filename, size.width, size.height)

        if fullpath:
            return wx.BitmapFromImage(wx.Image(fullpath))
        else:
            return wx.NullBitmap



