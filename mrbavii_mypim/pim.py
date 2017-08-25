""" Main PIM class and functions. """

__author__      =   "Brian Allen Vanderburg II"
__copyright__   =   "Copyright (C) 2017 Brian Allen Vanderburg II"
__license__     =   "Apache License 2.0"



from . import errors

import os


class Error(errors.Error):
    """ Error class for the Pim object. """
    pass


class Pim(object):
    """
    This object represents access to an instance of a PIM and it's data.
    It provides methods to access files/directories under the PIM's data,
    access database files in the form of Sqlite, as well as various other
    methods.
    """

    def __init__(self, directory):
        # Basic setup
        self._directory = directory
        self._models = {}
        self._listeners = {}

        # Next open/create each model
        import models

        for model in models.all_models:
            self._models[model.MODEL_NAME] = model(self)

    def isok(self):
        return self._opened

    def open(self):
        if os.path.isfile(self._file):
            pass # Read settings file
        else:
            pass # Create initial settings file

        self._opened = True
        return True

    def get_model(self, name):
        return self._models.get(name, None)


    def listen(self, event, model, callback):
        """ Register a listener for a given callback. """
        # TODO: store a weakref of the callback so if the instance
        # goes out of existance, the callback is not called.

        if not event in self._listeners:
            self._listeners[event] = []

        self._listeners[event].append(callback)

    def notify(self, event, *args, **kwargs):
        """ Call a listeners of an event. """
        if event in self._listeners:
            # Call each listener
            for listener in self._listeners[event]:
                listener(*args, **kwargs)

    def get_directory(self):
        return self._directory

    def get_data_directory(self, model=None):
        """ Return a search path of supplied data directories, ie templates, etc. """
        roots = [
            os.path.join(self._directory, "data"),
            # get user data directory
            os.path.jon(os.path.dirname(__file), "data")
        ]

        return (os.path.join(i, model.MODEL_NAME if model else "common") for i in roots)


    def get_storage_directory(self, model=None):
        """ Return the storage directory. IE where the model puts it's files. """
        return os.path.join(self._directory, model.MODEL_NAME if model else "common")

    def get_cache_directory(self, model=None):
        """ Return a cache directory. """
        return os.path.join(self._directory, "cache", model.MODEL_NAME if model else "common")

