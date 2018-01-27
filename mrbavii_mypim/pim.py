""" Main PIM class and functions. """

__author__      =   "Brian Allen Vanderburg II"
__copyright__   =   "Copyright (C) 2017 Brian Allen Vanderburg II"
__license__     =   "Apache License 2.0"


import os
import sqlite3

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
        self._log_fn = None
        self._models = {}

        self._db = None
        self._db_file = None
        self._transaction_level = 0
        self._error_in_trasaction = False

        self._pim_settings = {}
        self._schema_versions = {}

        # Create/open the database
        self._open()

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

        self._transaction_level -= 1
        if self._transaction_level == 0:
            # Commit or rollback main transaction
            if type is None:
                self._db.execute("COMMIT;")
            else:
                self._db.execute("ROLLBACK;")
        else:
            # Release or rollback to the save point
            if type is None:
                self._db.execute("RELEASE save;")
            else:
                self._db.execute("ROLLBACK TO save;")

        return False

    def _open(self):
        """ Open the database object. """
        
        self._db_file = os.path.join(self._directory, "pim.db")

        # set isolation_level=None to avoid exec auto-begin/auto-commit
        self._db = sqlite3.connect(
            self._db_file,
            isolation_level=None)

        self._db.row_factory = sqlite3.Row

        # Issue any pragmas needed
        self._db.execute("PRAGMA foreign_keys=1;")

        # Create our main tables
        with self:
            self._upgrade_tables()

    def get_schema_version(self, name):
        """ Get an object/schema version. """
        version = self._schema_versions.get(name)
        if version is not None:
            return int(version)
        return None

    def set_schema_version(self, name, version):
        """ Set an object/schema version. """
        with self as cursor:
            if version is None:
                cursor.execute(
                    """DELETE FROM
                        schema_versions
                    WHERE
                        name=?;""",
                    (name,)
                )
                self._schema_versions.pop(name, None)
            else:
                cursor.execute(
                    """INSERT OR REPLACE INTO
                        schema_versions (name, version)
                    VALUES
                        (?, ?);""",
                    (name, int(version))
                )
                self._schema_versions[name] = int(version)
            
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

    def _upgrade_tables(self):
        """ Create and/or upgrade the base tables. """

        with self as cursor:
            # Create tables
            cursor.execute(
                """CREATE TABLE IF NOT EXISTS pim_settings(
                    name TEXT UNIQUE,
                    value TEXT
                );"""
            )

            cursor.execute(
                """CREATE TABLE IF NOT EXISTS schema_versions(
                    name TEXT UNIQUE,
                    version INTEGER
                );"""
            )

            # load PIM settings
            cursor.execute(
                "SELECT name,value FROM pim_settings;"
            )
            for row in cursor:
                self._settings[row["name"]] = row["value"]

            # load schema versions
            cursor.execute(
                "SELECT name,version FROM schema_versions;"
            )
            for row in cursor:
                self._schema_versions[row["name"]] = row["version"]

            cursor.close()

            # Set table versions
            self.set_schema_version("main", 1)

