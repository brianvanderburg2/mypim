""" Model for storing notes. """

__author__      =   "Brian Allen Vanderburg II"
__copyright__   =   "Copyright (C) 2017 Brian Allen Vanderburg II"
__license__     =   "Apache License 2.0"

import os
import re

from .model import Model

from ..errors import Error

class NotesModel(Model):
    """ Represent a tree of notes. """
    MODEL_NAME="notes"

    # Valid name regex uses a literal space character to match a space but
    # not tabs/newlines.
    _valid_name_re = re.compile("^[A-Za-z0-9]+( [A-Za-z0-9]+)*$")

    def __init__(self, pim):
        """ Construct the notes model. """
        Model.__init__(self, pim)
        self._directory = pim.get_storage_directory(self)

        if not os.path.isdir(self._directory):
            try:
                os.makedirs(self._directory)
            except (IOError, OSError) as e:
                raise Error(str(e))

    def valid_name(self, name):
        """ Determine if a name is valid. """
        # A name may consist of alphanumeric characters and spaces.
        # Spaces are translated to underscores for file names.
        # Names may be case sensitive on some platforms.
        # It should not begin or end with a space, and should not
        # contain multiple consecutive spaces.
        return self._valid_name_re.match(name)

    def _path_to_file(self, path):
        return os.path.join(i.replace(" ", "_") for i in path)

    def _file_to_path_part(self, file):
        return file.replace("_", " ")

    def get_children(self, path=None):
        """" Return a list of full paths for each note under the parent. """
        results = []
        found = []

        if path:
            directory = os.path.join(self._directory, *(self._path_to_file(path)))
        else:
            directory = self._directory

        if not os.path.isdir(directory):
            return results

        for file in sorted(os.listdir(directory)):
            if file.startswith("."):
                continue

            fullfile = os.path.join(directory, file)
            if os.path.islink(fullfile):
                continue

            if os.path.isfile(fullfile):
                if not file.lower().endswith(".note"):
                    continue
                file = file[:-5]
            elif os.path.isdir(fullfile):
                pass
            else:
                continue

            name = self._file_to_path_part(file)
            if name in found or not self.valid_name(name):
                continue

            # Append the tuple of the path to the results
            results.append(tuple(path) + (name,) if path else (name,))
            found.append(name)

        return results

    def create_note(self, name, path=None):
        """ Create a new note under parent. """
        pass

    def read_note(self, path):
        """ Reach a given note based on the fullpath name. """
        pass

    def write_note(self, path, contents):
        pass

    def move_note(self, path, new_parent):
        pass

    def rename_note(self, path, new_name):
        pass

    def delete_note(self, path):
        pass

    def get_attachements(self, path, attachment=None):
        pass




