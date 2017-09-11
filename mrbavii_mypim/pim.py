""" Main PIM class and functions. """

__author__      =   "Brian Allen Vanderburg II"
__copyright__   =   "Copyright (C) 2017 Brian Allen Vanderburg II"
__license__     =   "Apache License 2.0"


import os

from mrbaviirc.pattern.listener import ListenerMixin

from . import errors

from . import platform



class Error(errors.Error):
    """ Error class for the Pim object. """
    pass


class Pim(ListenerMixin):
    """
    This object represents access to an instance of a PIM and it's data.
    It provides methods to access files/directories under the PIM's data,
    access database files in the form of Sqlite, as well as various other
    methods.
    """

    def __init__(self, directory):
        """ Create/open a PIM associated with a given directory. """

        ListenerMixin.__init__(self)

        # Basic setup
        self._directory = directory
        self._progress_fn = None
        self._models = {}

        # Next open/create each model
        import models

        for model in models.all_models:
            self._models[model.MODEL_NAME] = model(self)

    def get_model(self, name):
        """ Return the instance for a given model. """
        return self._models.get(name, None)

    def register_progress_function(self, callback=None):
        """ Register a progress function.
            The progress function can take two arguments.
                1. A message to be displayed
                2. A percentage of completion.
            The progress function can return:
                True for the caller to continue
                False for the caller to abort
        """
        self._progress_fn = callback

    def call_progress_function(self, message, percent):
        """ Call the progress function. """
        if self._progress_fn:
            return self._progress_fn(message, percent)
        else:
            return True

    def register_log_function(self, callback=None):
        """ Register a simple logging function.
            This function will be called when simple errors occur.
            The progress function takes the following arguments:
                1. The logging level
                2. A string describing the logging source
                3. A message
            The logging function return is ignored.
        """
        self._log_fn = callback

    def call_log_function(self, level, source, message):
        """ Call a logging function if registered. """
        if self._log_fn:
            self._log_fn(level, source, message)

    def get_directory(self):
        """ Return the PIM directory. """
        return self._directory

    def get_data_directories(self):
        """ Return a search path of supplied data directories, ie templates, etc. """
        dirs = (
            os.path.join(self._directory, "data"),
            platform.get_user_data_dir("mypim"),
            os.path.join(os.path.dirname(__file__), "data")
        )

        return dirs

    def get_storage_directory(self, model):
        """ Return the storage directory. IE where the model puts it's files. """
        return os.path.join(self._directory, model.MODEL_NAME)

    def get_cache_directory(self, model):
        """ Return a cache directory. """
        return os.path.join(self._directory, "cache", model.MODEL_NAME)

