""" Base view class. """

__author__      =   "Brian Allen Vanderburg II"
__copyright__   =   "Copyright (C) 2017 Brian Allen Vanderburg II"
__license__     =   "Apache License 2.0"


import wx


class View(wx.Panel):

    def __init__(self, parent, pim):
        
        wx.Panel.__init__(self, parent, wx.ID_ANY)
        self._pim = pim


    def get_icon(self):
        return None


