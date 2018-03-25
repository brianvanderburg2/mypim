""" Main application window. """

__author__      =   "Brian Allen Vanderburg II"
__copyright__   =   "Copyright (C) 2017 Brian Allen Vanderburg II"
__license__     =   "Apache License 2.0"


import wx

from mrbaviirc.gui.wx import bookctrl

class MainWindow(wx.Frame):

    def __init__(self, pim):
        wx.Frame.__init__(self, None, wx.ID_ANY, wx.GetApp().GetAppDisplayName() + " : " + pim.get_directory())

        self._pim = pim
        self.InitGui()

    def InitGui(self):

        # Register our listeners first
        self._pim.add_listener("view-restore", self.OnViewRestore)
        self._pim.add_listener("view-save", self.OnViewSave)

        # Log Window

        # Views
        self.views = bookctrl.ScrolledButtonBook(self, wx.ID_ANY, wx.LEFT, 3, -1)

        from . import views

        for view in views.all_views:
            view_window = view(self.views, self._pim)
            view_bitmap = wx.ArtProvider.GetBitmap(view.VIEW_ICON, size=(32, 32))
            self.views.AddPage(view_window, view.VIEW_NAME, view_bitmap)

        # Top sizer
        border= wx.SizerFlags.GetDefaultBorder()

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.SetMinSize((300, 300))
        sizer.AddF(self.views, wx.SizerFlags(1).Expand().Border(wx.ALL))

        self.SetSizerAndFit(sizer)
        self.SetAutoLayout(True)
        self.Layout()

        # Restore view classes
        self._pim.notify_listeners("view-restore")

        # Events
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnClose(self, event):
        self._pim.notify_listeners("view-save")

        self.Destroy()

    def OnViewRestore(self):
        config = wx.Config.Get()
        changer = wx.ConfigPathChanger(config, "/Views/MainWindow/")

        left = config.ReadInt("Left", -1)
        top = config.ReadInt("Top", -1)
        width = config.ReadInt("Width", -1)
        height = config.ReadInt("Height", -1)

        if left >= 0 and top >= 0:
            self.SetPosition((left, top))

        if width >= 0 and height >= 0:
            size = wx.Size(width, height)
            size.IncTo(self.GetMinSize())
            self.SetSize(size)

    def OnViewSave(self):
        config = wx.Config.Get()
        changer = wx.ConfigPathChanger(config, "/Views/MainWindow/")

        pos = self.GetPosition()
        size = self.GetSize()

        config.WriteInt("Left", pos.x) 
        config.WriteInt("Top", pos.y)
        config.WriteInt("Width", size.width)
        config.WriteInt("Height", size.height)


