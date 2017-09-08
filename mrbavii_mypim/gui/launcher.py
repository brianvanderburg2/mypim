""" Launcher to allow opening a given PIM. """

__author__      =   "Brian Allen Vanderburg II"
__copyright__   =   "Coryright (C) 2017 Brian Allen Vanderburg II"
__license__     =   "Apache License 2.0"


import wx


class LauncherDialog(wx.Dialog):
    """ Dialog to prompt for a given PIM or allow creation of a new PIM. """

    def __init__(self):
        """ Initialize the dialog. """
        wx.Dialog.__init__(self, None, wx.ID_ANY, "Choose PIM")

        self.result = None
        self.InitGui()

    def InitGui(self):
        """ Create the GUI. """

        # Widgets
        text = wx.StaticText(self, wx.ID_ANY, "Select a previous PIM to open from the list below, or a new PIM.")
        self.history = wx.ListBox(self, size=(300, 200))
        self.remember = wx.CheckBox(self, wx.ID_ANY, "Open the selected PIM at startup.")
        choose_button = wx.Button(self, wx.ID_ANY, "Choose")

        self.Bind(wx.EVT_BUTTON, self.OnNew, choose_button)
        self.Bind(wx.EVT_BUTTON, self.OnOk, id=wx.ID_OK)

        # Positions
        sizer = wx.BoxSizer(wx.VERTICAL)

        sizer.AddF(text, wx.SizerFlags(0).Expand().Border(wx.BOTTOM))
        sizer.AddF(self.history, wx.SizerFlags(1).Expand())
        sizer.AddF(self.remember, wx.SizerFlags(0).Expand().Align(wx.ALIGN_LEFT).Border(wx.BOTTOM))
        sizer.AddF(choose_button, wx.SizerFlags(0).Align(wx.ALIGN_RIGHT))

        btns = self.CreateSeparatedButtonSizer(wx.OK | wx.CANCEL)
        
        mainSizer = wx.BoxSizer(wx.VERTICAL)

        mainSizer.AddF(sizer, wx.SizerFlags(1).Expand().Border(wx.ALL))
        mainSizer.Add(btns, 0, wx.ALL | wx.EXPAND)
        self.SetSizerAndFit(mainSizer)

        # Load the list
        config = wx.Config.Get()

        history = wx.FileHistory()
        changer =  wx.ConfigPathChanger(config, "/History/")
        history.Load(config)
        changer = None

        for i in range(history.GetCount()):
            self.history.Append(history.GetHistoryFile(i))

        # Remember
        self.remember.SetValue(config.ReadBool("/OpenLast", False))

    def OnNew(self, event):
        " Browse for a directory and add to the list. """

        dir = wx.DirSelector("Choose PIM Directory")
        if(dir):
            index = self.history.Append(dir)
            self.history.SetSelection(index)

    def OnOk(self, event):
        index = self.history.GetSelection()
        if index >= 0:
            self.result = self.history.GetString(index)

        config = wx.Config.Get()

        # Save the History list
        history = wx.FileHistory()
        for i in reversed(range(self.history.GetCount())):
            history.AddFileToHistory(self.history.GetString(i))

        if self.result:
            history.AddFileToHistory(self.result)
        
        changer = wx.ConfigPathChanger(config, "/History/")
        history.Save(config)
        changer = None


        # Save the Current Item
        config.WriteBool("/OpenLast", self.remember.IsChecked())
        config.Write("/LastPIM", "") # It is set by the main window after open
        
        self.EndModal(wx.ID_OK)

    def GetResult(self):
        """ Return the selected item. """
        return self.result







