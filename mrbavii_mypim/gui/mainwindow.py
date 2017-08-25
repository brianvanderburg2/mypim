""" Main application window. """

__author__      =   "Brian Allen Vanderburg II"
__copyright__   =   "Copyright (C) 2017 Brian Allen Vanderburg II"
__license__     =   "Apache License 2.0"


import wx

from ..pim import Pim

class MainWindow(wx.Frame):

    def __init__(self, directory):
        wx.Frame.__init__(self, None, wx.ID_ANY, "Main Window")

        self._pim = Pim(directory)
        self.create_widgets()




    def create_widgets(self):

        # General window settings
        panel = wx.Panel(self)

        # Menu Bar
        # Tool Bar
        bar = self.CreateToolBar()


        # Status Bar
        bar = self.CreateStatusBar()
        self.SetStatusBar(bar)

        # Log Window

        # Views
        view_images = wx.ImageList(32, 32)

        self.views = wx.Listbook(panel, wx.ID_ANY)

        self.views.AssignImageList(view_images)

        from . import views

        for view in views.all_views:
            view_window = view(self.views, self._pim)
            image_index = view_images.AddIcon(view_window.get_icon())
            self.views.AddPage(view_window, view.VIEW_NAME, False, image_index)

        for i in range(50):
            self.views.AddPage(wx.Panel(self.views, wx.ID_ANY), "Test", False, image_index)

        # Sizers
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.AddF(self.views, wx.SizerFlags(1).Expand().Border(wx.ALL))
        
        panel.SetSizerAndFit(sizer)
        panel.SetAutoLayout(True)



        # Top sizer
        border= wx.SizerFlags.GetDefaultBorder()

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.SetMinSize((300, 300))
        sizer.AddF(panel, wx.SizerFlags(1).Expand().Border(wx.ALL))

        self.SetSizerAndFit(sizer)
        self.SetAutoLayout(True)
        self.Layout()

