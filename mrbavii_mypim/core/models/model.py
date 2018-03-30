""" Base model class. """

__author__      =   "Brian Allen Vanderburg II"
__copyright     =   "Copyright (C) 2017 Brian Allen Vanderburg II"
__license__     =   "Apache License 2.0"

from collections import OrderedDict

class Model(object):
    """ Base class for a model. """

    def __init__(self, pim):
        """ Construct the model. """
        self._pim = pim

    def open(self):
        pass

    def isok(self):
        return False

class ModelInstaller(object):
    """ Base class for a model installer/updater. """

    def __init__(self, model):
        self._model = model
        self._pim = model._pim

    def install(self):
        """ Use the version map to execute the install functions. """
        version = self._pim.get_model_version(self._model.MODEL_NAME)
        while True:
            callback = self._install_map.get(version)
            if callback:
                version = callback(self)
            else:
                break
        self._pim.set_model_version(self._model.MODEL_NAME, version)
