""" Base model class. """

__author__      =   "Brian Allen Vanderburg II"
__copyright     =   "Copyright (C) 2017 Brian Allen Vanderburg II"
__license__     =   "Apache License 2.0"

from collections import OrderedDict

class Model(object):
    """ Base class for a model. """

    # Expected to be the registered name of the model
    MODEL_NAME=None

    # INTEGER version number of the model, used to test for upgrades
    MODEL_VERSION=None

    # List of dependency models
    MODEL_DEPENDS=[]

    def __init__(self, db):
        """ Construct the model. """
        self._db = db

    def check_install(self):
        """ Return if the model needs installed/upgraded. """
        return self._db.get_model_version(self.MODEL_NAME) != self.MODEL_VERSION

    def install(self):
        pass

    def open(self):
        pass

    def isok(self):
        return False


class ModelInstaller(object):
    """ Base class for a model installer/updater. """

    _install_map = None

    def __init__(self, model):
        self._model = model
        self._db = model._db

    def get_version(self):
        return self._db.get_model_version(self._model.MODEL_NAME)

    def set_version(self, version):
        self._db.set_model_version(self._model.MODEL_NAME, version)

    def install(self):
        """ Use the version map to execute the install functions. """
        while True:
            version = self._db.get_model_version(self._model.MODEL_NAME)
            callback = self._install_map.get(version)
            if callback:
                callback(self)
            else:
                break


