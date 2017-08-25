""" Notes view """

__author__      =   "Brian Allen Vanderburg II"
__copyright__   =   "Copyright (C) 2017 Brian Allen Vanderburg II"
__license__     =   "Apache License 2.0"


import wx
import wx.html


from .view import View

class NotesView(View):
    VIEW_NAME = "Notes"

    def __init__(self, parent, pim):
        View.__init__(self, parent, pim)
        self._model = pim.get_model("notes")

        self.init_gui()

    def get_icon(self):
        return wx.ArtProvider.GetIcon(wx.ART_ERROR, size=(32, 32))


    def init_gui(self):
        # Create the basic GUI
        self.splitter = wx.SplitterWindow(self)

        self.tree = wx.TreeCtrl(self.splitter, wx.ID_ANY, style=wx.TR_HIDE_ROOT | wx.TR_HAS_BUTTONS | wx.TR_LINES_AT_ROOT)
        self.tabs = wx.Notebook(self.splitter, wx.ID_ANY)

        self.view = wx.html.HtmlWindow(self.tabs, wx.ID_ANY)
        self.source = wx.TextCtrl(self.tabs, wx.ID_ANY, style=wx.TE_MULTILINE | wx.TE_PROCESS_ENTER | wx.TE_PROCESS_TAB | wx.HSCROLL)

        self.tabs.AddPage(self.view, "View")
        self.tabs.AddPage(self.source, "Edit")

        self.splitter.SplitVertically(self.tree, self.tabs)
        self.splitter.SetMinimumPaneSize(20)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.splitter, 1, wx.EXPAND | wx.ALL, 5)
        self.SetSizerAndFit(sizer)

        # Events
        self.Bind(wx.html.EVT_HTML_LINK_CLICKED, self.OnClick)

        # Initialize
        self.refresh_tree()

    def refresh_tree(self):
        # self.set_selection(None)
        self.tree.DeleteAllItems()

        root_item = self.tree.AddRoot("")

        children = self._model.get_children()
        for child in children:
            name = child[-1]
            child_item = self.tree.AppendItem(root_item, name, data=wx.TreeItemData(child))
            has_children = self._model.get_children(child)
            self.tree.SetItemHasChildren(child_item, len(has_children) > 0)








    def OnClick(self, evt):
        wx.MessageBox(evt.GetLinkInfo().GetHref(), "Title", parent=self)
        pass
