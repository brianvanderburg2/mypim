""" Application class. """

__author__      =   "Brian Allen Vanderburg II"
__copyright__   =   "Copyright (C) 2017 Brian Allen Vanderburg II"
__license__     =   "Apache License 2.0"

import sys
import os

import wx
import wx.html # Notes mention this should be imported before the wx.App is created

#from mrbaviirc import app
from mrbaviirc.gui.wx.art import ArtProvider

from mrbavii_mypim.core.pim import Pim, PimAppHelper

from .mainwindow import MainWindow



class GuiApp(wx.App):

    def __init__(self, helper):
        self._helper = helper

        # Needs to be called last b/c it calls OnInit
        wx.App.__init__(self)

    def OnInit(self):
        # Set up common stuff
        self.SetAppName(self._helper.appname)
        self.SetAppDisplayName(self._helper.displayname)

        # directory setup
        self._path = self._helper.traits.path

        confdir = self._path.get_user_config_dir()
        if not os.path.isdir(confdir):
            os.makedirs(confdir)

        # TODO: wxStandardPaths wrapper around platform.Path

        # Create our art provider
        art = ArtProvider(
            os.path.join(
                self._path.get_package_data_dir(
                    sys.modules[".".join(__name__.split('.')[:-2])], all=False
                ),
                "icons"
            )
        )
        wx.ArtProvider.Push(art)

        # Create the Config object
        # TODO: Create a custom config object in mrbaviirc, then
        # a wxConfigBase wrapper around it
        config = wx.FileConfig(
            self.GetAppName(),
            self.GetVendorName(),
            os.path.join(
                self._path.get_user_config_dir(),
                "mypim.conf"
            ),
            wx.EmptyString,
            wx.CONFIG_USE_LOCAL_FILE
        )
        wx.Config.Set(config)

        # Show launcher or open previous PIM
        last = config.Read("LastPim")
        if last and os.path.isdir(last):
            return self.Open(last)
        else:
            return self.Launcher()

    def Open(self, directory):

        if not os.path.isdir(directory):
            return False

        # Establish connection to PIM:
        pim = Pim(self._helper, directory)
        pim.connect()

        if pim.check_install():
            pim.install() # TODO prompt user first, and wrap in progress dialog

        # Open the PIM, showing a progrss dialog
        dlg = wx.ProgressDialog("Open", "Opening " + directory)
        def progress_callback(msg, pct):
            dlg.Pulse()

        pim.register_progress_function(progress_callback)
        pim.open()
        pim.register_progress_function(None)
        dlg.Destroy()

        # Create and show the main window
        window = MainWindow(pim)
        
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

    def Upgrade(self, pim):
        pass


class GuiAppHelper(PimAppHelper):

    def gui_main(self):
        guiapp = GuiApp(self)
        guiapp.MainLoop()


def main():
    app = GuiAppHelper()
    app.execute()

