""" Model for storing notes. """

__author__      =   "Brian Allen Vanderburg II"
__copyright__   =   "Copyright (C) 2017 Brian Allen Vanderburg II"
__license__     =   "Apache License 2.0"


"""
Notes storage format.

Each note is essentially a dirctory under the notes storage.  The name
of the note is based on the directory name.  The actual note content
is stored in a file called "contents.note" in the given directory. The
advantage of this is that to move or rename a note only requires moving
that directory as all attachments and sub-notes are part of the directory.
"""


import os
import re
import io
import shutil

try:
    from xml.etree import cElementTree as ET
except ImportError:
    from xml.etree import ElemenetTree as ET

from mrbaviirc import template
from mrbaviirc.template.lib.xml import ElementTreeWrapper

from ... import util
from .model import Model, ModelInstaller
from ...errors import Error

class NotesModel(Model):
    """ Represent a tree of notes. """
    MODEL_NAME="notes"
    NOTE_FILENAME="contents.note"

    # Valid name regex uses a literal space character to match a space but
    # not tabs/newlines.
    _valid_name_re = re.compile("^[A-Za-z0-9]+( [A-Za-z0-9]+)*$")

    def __init__(self, pim):
        """ Construct the notes model. """
        Model.__init__(self, pim)
        self._directory = pim.get_storage_directory(self)

    def open(self):
        if not os.path.isdir(self._directory):
            try:
                os.makedirs(self._directory)
            except (IOError, OSError) as e:
                raise Error(str(e))

        installer = NotesModelInstaller(self)
        installer.install()

    def valid_name(self, name):
        """ Determine if a name is valid. """
        # A name may consist of alphanumeric characters and spaces.
        # Spaces are translated to underscores for file names.
        # Names may be case sensitive on some platforms.
        # It should not begin or end with a space, and should not
        # contain multiple consecutive spaces.
        return self._valid_name_re.match(name)

    def valid_path(self, path):
        """ Return if a path is valid. """
        return isinstance(path, (list, tuple)) and all(self.valid_name(i) for i in path)

    def _path_to_file(self, path):
        return os.path.join(i.replace(" ", "_") for i in path)

    def _file_to_path_part(self, file):
        return file.replace("_", " ")

    def _get_note_dir_file(self, path=None):
        if path is None:
            return (self._directory, None)
        else:
            if not self.valid_path(path):
                raise Error("Invalid note path.")

            directory = os.path.join(self._directory, *(self._path_to_file(path)))
            file = os.path.join(directory, self.NOTE_FILENAME)

            return (directory, file)

    def get_children(self, path=None):
        """" Return a list of full paths for each note under the parent. """
        results = []
        found = []

        (directory, _) = self._get_note_dir_file(path)
        if not os.path.isdir(directory):
            return results

        for file in sorted(os.listdir(directory)):
            if file.startswith("."):
                continue

            fullfile = os.path.join(directory, file)
            if os.path.islink(fullfile) or not os.path.isdir(fullfile):
                continue

            name = self._file_to_path_part(file)
            if name in found or not self.valid_name(name):
                continue

            # Append the tuple of the path to the results
            results.append(tuple(path) + (name,) if path else (name,))
            found.append(name)

        return results

    def get_attachments(self, path, attachment=None):
        """ Return the attachment directory for a given note. """
        (directory, file) = self._get_note_dir_file(path)
        return directory

    def create_note(self, path):
        """ Create a new note. """
        (directory, file) = self._get_note_dir_file(path)
        if os.path.isfile(file):
            raise Error("Note already exists")

        try:
            os.makedirs(directory)
            with io.open(file, "wt", newline=None) as handle:
                handle.write(u"<note></note>")
        except (IOError, OSError) as e:
            raise Error(str(e))

        return path

    def read_note(self, path):
        """ Read a given note based on the fullpath name. """
        (directory, file) = self._get_note_dir_file(path)
        if not os.path.isfile(file):
            raise Error("Note does not exist.")

        if not os.path.exists(file):
            return ""

        try:
            with io.open(file, "rt", newline=None) as handle:
                return handle.read()
        except (IOError, OSError) as e:
            raise Error(str(e))

    def write_note(self, path, contents):
        """ Save a given note. """
        (directory, file) = self._get_note_dir_file(path)
        if not os.path.isdir(directory):
            raise Error("No such note")

        try:
            with io.open(file, "wt", newline=None) as handle:
                handle.write(contents)
        except (IOError, OSError) as e:
            raise Error(str(e))

    def move_note(self, path, new_parent):
        """ Move a note to a new parent. """
        new_path = tuple(new_parent) + (path[-1],)

        (o_dir, _) = self._get_note_dir_file(path)
        (n_dir, _) = self._get_note_dir_file(new_path)

        if os.path.exists(n_dir):
            raise Error("Destination already exists")

        try:
            os.rename(o_dir, n_dir)
        except (IOError, OSError) as e:
            raise Error(str(e))

        return new_path

    def rename_note(self, path, new_name):
        """ Rename a note in the current path. """
        new_path = tuple(path[:-1]) + (new_name,)

        (o_dir, _) = self._get_note_dir_file(path)
        (n_dir, _) = self._get_note_dir_file(new_path)

        if os.path.exists(n_dir):
            raise Error("Destination already exists")

        try:
            os.rename(o_dir, n_dir)
        except (IOError, OSError) as e:
            raise Error(str(e))

        return new_path

    def delete_note(self, path):
        """ Delete a note. """
        (o_dir, _) = self._get_note_dir_file(path)

        try:
            shutil.rmtree(o_dir)
            return
        except (IOError, OSError) as e:
            raise Error(str(e))

    def parse_note(self, path):
        """ Parse note into HTML. """
        # This sould possible be with the view instead the model

        (_, file) = self._get_note_dir_file(path)
        if not os.path.isfile(file):
            return # Error if note file doesn't exist?

        try:
            xml = ET.parse(file)
            root = xml.getroot()

            context = {
                "xml": ElementTreeWrapper(root)
            }

            paths = map(lambda i: os.path.join(i, "templates"), self._pim.get_data_directories())
            loader = template.SearchPathLoader(paths)
            env = template.Environment(loader=loader)

            renderer = template.StringRenderer()
            tmpl = env.load_file("notes/main.tmpl")
            tmpl.render(renderer, context)
        except Exception as e:
            raise Error(str(e))

        return renderer.get()


class NotesModelInstaller(ModelInstaller):
    """ Handle install/upgrades for the notes model. """

    _install_map = {
    }

