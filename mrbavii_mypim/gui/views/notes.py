""" Notes view """

__author__      =   "Brian Allen Vanderburg II"
__copyright__   =   "Copyright (C) 2017 Brian Allen Vanderburg II"
__license__     =   "Apache License 2.0"


import wx
import wx.html

from .view import View
from ...errors import Error


class NotesView(View):
    VIEW_NAME = "Notes"
    VIEW_ICON = "notes"

    def __init__(self, parent, pim):
        View.__init__(self, parent, pim)
        self._model = pim.get_model("notes")
        self._current_note = None

        self.InitGui()

    def InitGui(self):
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
        self.Bind(wx.html.EVT_HTML_LINK_CLICKED, self.OnLinkClick)
        self.Bind(wx.EVT_TREE_SEL_CHANGING, self.OnNoteChanging, self.tree)
        self.Bind(wx.EVT_TREE_SEL_CHANGED, self.OnNoteChanged, self.tree)
        self.Bind(wx.EVT_TREE_ITEM_EXPANDING, self.OnNoteExpand, self.tree)
        self.Bind(wx.EVT_TREE_ITEM_COLLAPSED, self.OnNoteCollapse, self.tree)
        self.Bind(wx.EVT_CONTEXT_MENU, self.OnNoteMenu, self.tree)
        
        # Create our popup menu
        menu = self.treeMenu = wx.Menu()

        newroot = menu.Append(wx.ID_ANY, "New Root")
        newchild = menu.Append(wx.ID_ANY, "New Child")
        rename = menu.Append(wx.ID_ANY, "Rename")
        delete = menu.Append(wx.ID_ANY, "Delete")

        self.Bind(wx.EVT_MENU, self.OnNewRoot, newroot)
        self.Bind(wx.EVT_MENU, self.OnNewChild, newchild)
        self.Bind(wx.EVT_MENU, self.OnRename, rename)
        self.Bind(wx.EVT_MENU, self.OnDelete, delete)

        # Initialize
        self.RefreshTree()

    def PopulateTree(self, item):
        # Determine the items note
        data = self.tree.GetItemData(item)
        if not data:
            return

        note = data.GetData()
        children = self._model.get_children(note)
        for child in children:
            name = child[-1]
            child_item = self.tree.AppendItem(item, name, data=wx.TreeItemData(child))
            has_children = self._model.get_children(child)
            self.tree.SetItemHasChildren(child_item, len(has_children) > 0)
        self.tree.SortChildren(item)

    def RefreshTree(self):
        # self.set_selection(None)
        self.tree.DeleteAllItems()

        root_note = ()
        root_item = self.tree.AddRoot("Notes", data=wx.TreeItemData(root_note))
        self.PopulateTree(root_item)

    def QuerySave(self):
        if not (self._current_note and self.source.IsModified()):
            return True

        note = "/".join(self._current_note)
        answer = wx.MessageBox("Note has been changed.  Save?\n{0}".format(note), "Question", wx.YES_NO, parent=self)
        if answer == wx.YES:
            return self.Save()
        elif answer == wx.NO:
            return True # Use selected not to save, continue action
            
    def Save(self):
        if not self._current_note:
            wx.LogError("No current note to save.")

        contents = self.source.GetValue()
        try:
            self._model.write_note(self._current_note, contents)
        except Error as e:
            wx.LogError(str(e))
            return False

        self.source.SetModified(False)
        return True

    def ResetNote(self):
        self.source.SetValue("")
        self.view.SetPage("<html></html>")
        self._current_note = None
        self.source.SetModified(False)

    def ShowNote(self, note):
        self.ResetNote()

        try:
            # Always show the source
            contents = self._model.read_note(note)
            self.source.SetValue(contents)
            self.source.SetModified(False)
            self._current_note = note

            # Try to show the result
            html = self._model.parse_note(note)
            self.view.SetPage(html)
        except Error as e:
            wx.LogError(str(e))

    def OnLinkClick(self, evt):
        #wx.MessageBox(evt.GetLinkInfo().GetHref(), "Title", parent=self)
        evt.Skip()
        pass

    def OnNoteChanging(self, evt):
        if not self.QuerySave():
            evt.Veto()

    def OnNoteChanged(self, evt):
        self.ResetNote()
        
        item = evt.GetItem();
        if not item.IsOk():
            return

        # TreeItemData from tree
        note = self.tree.GetItemData(item)
        if not note:
            return

        # Data from tree item data
        note = note.GetData()

        self.ShowNote(note)

    def OnNoteExpand(self, evt):
        item = evt.GetItem()
        if not item.IsOk():
            return

        self.PopulateTree(item)

    def OnNoteCollapse(self, evt):
        item = evt.GetItem()
        if not item.IsOk():
            return

        self.tree.DeleteChildren(item)

    def OnNoteMenu(self, evt):
        self.PopupMenu(self.treeMenu)

    def OnNewRoot(self, evt):
        if not self.QuerySave():
            return

        self.DoNewNote(self.tree.GetRootItem())
            
    def OnNewChild(self, evt):
        if not self.QuerySave():
            return

        self.DoNewNote(self.tree.GetSelection())

    def DoNewNote(self, parent):
        data = self.tree.GetItemData(parent)
        if not data:
            return

        parent_note = data.GetData()
        if parent_note is None:
            return
        
        newname = wx.GetTextFromUser(
            "New note name:",
            "New Note",
            "Name",
            parent=self
        )

        if not newname:
            return

        # Expand before creating the new note so adding an item if it's not already
        # expanded won't result in a duplicate item (one from expansion and one added)
        if not self.tree.IsExpanded(parent):
            self.tree.SetItemHasChildren(parent, True) # Item must have children to expand
            self.tree.Expand(parent)

        try:
            newnote = tuple(parent_note) + (newname,)
            newnote = self._model.create_note(newnote)
        except Error as e:
            wx.LogError(str(e))
            return

        child = self.tree.AppendItem(parent, newname, data=wx.TreeItemData(newnote))
        self.tree.SortChildren(parent)
        self.tree.SelectItem(child)
            


    def OnRename(self, evt):
        item = self.tree.GetSelection()
        if not item or not item.IsOk():
            return

        data = self.tree.GetItemData(item)
        if not data:
            return

        note = data.GetData()
        if not note:
            return

        newname = wx.GetTextFromUser(
            "Rename: {0}".format("/".join(note)),
            "Rename Note",
            note[-1],
            parent=self)
        
        if not newname or newname == note[-1]:
            return

        try:
            newnote = self._model.rename_note(note, newname)
        except Error as e:
            wx.LogError(str(e))
            return

        self.tree.CollapseAndReset(item)
        self.tree.SetItemData(item, wx.TreeItemData(newnote))
        self.tree.SetItemText(item, newname)

        parent = self.tree.GetItemParent(item)
        self.tree.SortChildren(parent)


    def OnDelete(self, evt):
        if not self.QuerySave():
            return

        item = self.tree.GetSelection()
        if not item or not item.IsOk():
            return

        data = self.tree.GetItemData(item)
        if not data:
            return

        note = data.GetData()
        if not note:
            return

        answer = wx.MessageBox(
            "Really delete note '{0}' with all child notes and attachments?  This cannot be undone.".format("/".join(note)),
            "Delete",
            wx.YES_NO,
            parent=self
        )
        if answer != wx.YES:
            return

        try:
            newnote = self._model.delete_note(note)
        except Error as e:
            wx.LogError(str(e))
            return

        self.ResetNote()
        self.tree.Delete(item)

    def DoViewRestore(self, config):
        position = config.ReadInt("SashPosition", 40)
        self.splitter.SetSashPosition(position)

    def DoViewSave(self, config):
        config.WriteInt("SashPosition", self.splitter.GetSashPosition())



