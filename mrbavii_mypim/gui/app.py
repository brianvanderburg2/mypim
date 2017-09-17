""" Application class. """

__author__      =   "Brian Allen Vanderburg II"
__copyright__   =   "Copyright (C) 2017 Brian Allen Vanderburg II"
__license__     =   "Apache License 2.0"

import os

import wx
import wx.html # Notes mention this should be imported before the wx.App is created

from .mainwindow import MainWindow
from .art import ArtProvider

class App(wx.App):
    def OnInit(self):
        # Set up common stuff
        self.SetAppName("mrbavii-mypim")

        # Check for a single instance
        self.instance = wx.SingleInstanceChecker(self.GetAppName())
        if self.instance.IsAnotherRunning():
            wx.MessageBox("Another instance of {0} is running.".format(self.GetAppName()), "ERROR")
            return False

        # Create our art provider
        art = ArtProvider(
            os.path.join(
                os.path.dirname(__file__),
                "..", "data", "icons"
            )
        )
        wx.ArtProvider.Push(art)

        # Standard paths
        paths = wx.StandardPaths.Get()

        # Create the Config object
        config = wx.FileConfig(self.GetAppName(), self.GetVendorName())
        wx.Config.Set(config)

        # Show launcher or open previous PIM
        last = config.Read("LastPim")
        if last and os.path.isdir(last):
            return self.Open(last)
        else:
            return self.Launcher()

    def Open(self, directory):
        import os

        if not os.path.isdir(directory):
            return False

        from .mainwindow import MainWindow

        window = MainWindow(directory)
        
        window.Show(True)
        self.SetTopWindow(window)

        return True

    def Launcher(self):
        from .launcher import LauncherDialog

        launcher = LauncherDialog()
        if launcher.ShowModal() == wx.ID_OK:
            result = launcher.GetResult()
            launcher.Destroy()
            return self.Open(result)
        else:
            launcher.Destroy
            return False

        
def main():
    app = App()
    app.MainLoop()

