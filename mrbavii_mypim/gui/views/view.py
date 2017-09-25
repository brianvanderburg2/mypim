""" Base view class. """

__author__      =   "Brian Allen Vanderburg II"
__copyright__   =   "Copyright (C) 2017 Brian Allen Vanderburg II"
__license__     =   "Apache License 2.0"


import wx


class View(wx.Panel):
    VIEW_NAME = "ViewName"
    VIEW_LINK = "linkname"
    VIEW_ICON = "iconname"

    def __init__(self, parent, pim):
        
        wx.Panel.__init__(self, parent, wx.ID_ANY)
        self._pim = pim

        self._pim.add_listener("view-restore", self.OnViewRestore)
        self._pim.add_listener("view-save", self.OnViewSave)

    def OnViewRestore(self):
        config = wx.Config.Get()
        changer = wx.ConfigPathChanger(config, "/Views/" + self.VIEW_NAME + "/")

        self.DoViewRestore(config)

    def OnViewSave(self):
        config = wx.Config.Get()
        changer = wx.ConfigPathChanger(config, "/Views/" + self.VIEW_NAME + "/")

        self.DoViewSave(config)

    def DoViewRestore(self, config):
        pass

    def DoViewSave(self, config):
        pass





