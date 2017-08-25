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


