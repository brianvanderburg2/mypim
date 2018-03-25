""" Main PIM class and functions. """

__author__      =   "Brian Allen Vanderburg II"
__copyright__   =   "Copyright (C) 2017 Brian Allen Vanderburg II"
__license__     =   "Apache License 2.0"


import os
import sqlite3

import gzip
import datetime
import shutil

from mrbaviirc.pattern.listener import ListenerMixin
from mrbaviirc.util import FileMover

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
        """ Create a PIM associated with a given directory. """

        ListenerMixin.__init__(self)

        # Basic setup
        self._directory = directory
        self._progress_fn = None
        self._log_fn = None
        self._models = {}

        self._db = None
        self._db_file = None
        self._transaction_level = 0
        self._error_in_trasaction = False

        self._pim_settings = {}
        self._model_versions = {}

        from . import models
        for model in models.all_models:
            self._models[model.MODEL_NAME] = model(self)

    def get_model(self, name):
        """ Return the instance for a given model. """
        return self._models.get(name, None)

    def _db_progress_handler(self):
        """ Called by sqlite3 every so many instructions. """
        self.call_progress_function(None, None)

    def register_progress_function(self, callback=None):
        """ Register a progress function.
            The progress function can take two arguments.
                1. A message to be displayed, can be empty string/None
                2. A percentage of completion, can be None if unknown
            The progress function can return:
                True for the caller to continue
                False for the caller to abort if possible.
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
            #platform.get_user_data_dir("mrbavii-mypim"),
            os.path.join(os.path.dirname(__file__), "data")
        )

        return dirs

    def get_storage_directory(self, model):
        """ Return the storage directory. IE where the model puts it's files. """
        return os.path.join(self._directory, model.MODEL_NAME)

    def get_cache_directory(self, model):
        """ Return a cache directory. """
        return os.path.join(self._directory, "cache", model.MODEL_NAME)

    def get_export_directory(self, model):
        """ Return the export directory. """
        return os.path.join(self._directory, "export", model.MODEL_NAME)

    # Database related code
    #######################
    
    def __enter__(self):
        """ Begin a transaction, support nested context calls. """

        if self._transaction_level == 0:
            # Just now starting transaction
            self._db.execute("BEGIN IMMEDIATE;")
        else:
            # Already in transaction, make a nested savepoint
            self._db.execute("SAVEPOINT save;")
        
        self._transaction_level += 1
        return self._db.cursor()

    def __exit__(self, type, value, traceback):
        """ Commit or rollback on leaving the context. """

        if self._transaction_level == 1:
            # Commit or rollback main transaction
            if type is None:
                try:
                    self._db.execute("COMMIT;")
                    self._transaction_level -= 1
                except: # TODO: specify exception type
                    self._db.execute("ROLLBACK;")
                    self._transaction_level -= 1
                    raise
            else:
                self._db.execute("ROLLBACK;")
                self._transaction_level -= 1
        else:
            # Release or rollback to the save point
            if type is None:
                try:
                    self._db.execute("RELEASE save;")
                    self._transaction_level -= 1
                except: # TODO: specify exception type
                    self._db.execute("ROLLBACK to save;")
                    self._transaction_level -= 1
                    raise
            else:
                self._db.execute("ROLLBACK TO save;")
                self._transaction_level -= 1

        # If an exception was passed in, reraise it
        return False

    def open(self):
        """ Open the PIM, database, and models. """
        
        self._db_file = os.path.join(self._directory, "pim.db")

        # Set isolation_level=None to avoid exec auto-begin/auto-commit
        self._db = sqlite3.connect(
            self._db_file,
            isolation_level=None,
            cached_statements=1000)

        self._db.row_factory = sqlite3.Row
        self._db.set_progress_handler(self._db_progress_handler, 10000)

        # Issue any pragmas needed
        self._db.execute("PRAGMA foreign_keys=1;")

        # We require model_versions before installing
        with self as cursor:
            cursor.execute(
                """CREATE TABLE IF NOT EXISTS model_versions(
                    name TEXT UNIQUE,
                    version INTEGER
                );"""
            )
            cursor.execute(
                "SELECT name,version FROM model_versions;"
            )
            for row in cursor:
                self._model_versions[row["name"]] = row["version"]

            cursor.close()

        # Install/upgrade
        installer = PimInstaller(self)
        installer.install()

        # Load PIM settings
        with self as cursor:
            cursor.execute(
                "SELECT name,value FROM pim_settings;"
            )
            for row in cursor:
                self._settings[row["name"]] = row["value"]
            cursor.close()

        # Next open/create each model
        from . import models
        for model in models.all_models:
            self._models[model.MODEL_NAME].open()

    def backup(self):
        """ Backup the current database file. """

        # We must not be in a transaction
        if self._transaction_level > 0:
            raise Error("Backup cannot be complete while a transaction is in progress.")

        try:
            # Lock the database
            self._db.execute("BEGIN IMMEDIATE;")

            # Ensure backup directory exists
            backup_directory = os.path.join(self._directory, "backups")

            if not os.path.exists(backup_directory):
                os.makedirs(backup_directory)

            # Backup filename based on time
            now = datetime.datetime.utcnow()
            backup_basename = now.strftime("%Y%m%d-%H%M%S") + ".gz"
            backup_filename = os.path.join(backup_directory, backup_basename)

            # Compress as we back up
            with FileMover(backup_filename, backup_filename + ".tmp") as mover:
                with gzip.GzipFile(backup_filename + ".tmp", "wb", 9) as gzfile:
                    with open(self._db_file, "rb") as dbfile:
                        shutil.copyfileobj(dbfile, gzfile)

                mover.commit()
        finally:
            self._db.execute("ROLLBACK;")

    def get_model_version(self, name):
        """ Get a model version. """
        version = self._model_versions.get(name)
        if version is not None:
            return int(version)
        return None

    def set_model_version(self, name, version):
        """ Set a model version. """
        with self as cursor:
            if version is None:
                cursor.execute(
                    """DELETE FROM
                        model_versions
                    WHERE
                        name=?;""",
                    (name,)
                )
                self._model_versions.pop(name, None)
            else:
                cursor.execute(
                    """INSERT OR REPLACE INTO
                        model_versions (name, version)
                    VALUES
                        (?, ?);""",
                    (name, int(version))
                )
                self._model_versions[name] = int(version)
            
    def get_pim_setting(self, name):
        """ Get a PIM setting. """
        return self._pim_settings.get(name)

    def set_pim_setting(self, name, value):
        """ Set a PIM setting. """
        with self as cursor:
            if value is None:
                cursor.execute(
                    """DELETE FROM
                        pim_settings
                    WHERE
                        name=?;""",
                    (name,)
                )
                self._pim_settings.pop(name, None)
            else:
                cursor.execute(
                    """INSERT OR REPLACE INTO
                        pim_settings (name, value)
                    VALUES
                        (?, ?);""",
                    (name, value)
                )
                self._pim_settings[name] = value


class PimInstaller(object):
    """ Installer for the base PIM object. """
    def __init__(self, pim):
        self._pim = pim

    def install(self):
        """ Use the version map to execute the install fuctions. """
        version = self._pim.get_model_version("main")
        while True:
            callback = self._install_map.get(version)
            if callback:
                version = callback(self)
            else:
                break
        self._pim.set_model_version("main", version)

    def do_install(self):
        """ This is the main install. """
        with self._pim as cursor:
            # Note: model_versions never changes, just a name/version map
            # and is created if it doesn't exist already on the datbase open

            # pim_settings
            cursor.execute(
                """CREATE TABLE IF NOT EXISTS pim_settings(
                    name TEXT UNIQUE,
                    value TEXT
                );"""
            )

        # Installed to version 1
        return 1

    _install_map = {
        None: do_install
    }


