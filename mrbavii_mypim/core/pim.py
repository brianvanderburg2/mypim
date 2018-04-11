""" Main PIM class and functions. """

__author__      =   "Brian Allen Vanderburg II"
__copyright__   =   "Copyright (C) 2017 Brian Allen Vanderburg II"
__license__     =   "Apache License 2.0"


import sys
import os
import sqlite3
import argparse
import gzip
import datetime
import shutil

from collections import OrderedDict

from mrbaviirc.pattern.listener import ListenerMixin
from mrbaviirc.util import FileMover
from mrbaviirc import app

from . import errors


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

    def __init__(self, app, directory):
        """ Create a PIM associated with a given directory. """

        ListenerMixin.__init__(self)

        # Basic setup
        self._app = app
        self._directory = directory
        self._progress_fn = None
        self._log_fn = None
        self._fatal_error_fn = None
        self._models = OrderedDict()

        self._db = None
        self._db_file = None
        self._transaction_level = 0
        self._transation_cleanup_fns = []
        self._error_in_trasaction = False

        from . import models
        for model in models.all_models:
            self._models[model.MODEL_NAME] = model(self)

    def isreal(self):
        """ Return if  the PIM is real.  A real PIM has an associated
            directory and database.  An unreal PIM has no directory or
            database and is just used for callin the entry points. """
        return self._directory is not None

    def get_model(self, name):
        """ Return the instance for a given model. """
        return self._models.get(name, None)

    def get_model_entries(self):
        """ Return all available entry points. """
        entries = []
        for model in self._models:
            entries.extend(self._models[model].get_entries())

        return entries

    def call_model_entry(self, entry, params):
        """ Call an entry point. """
        for model in self._models:
            if entry in self._models[model].get_entries():
                return self._models[model].call_entry(entry, params)

        raise Error("No such entry: {}".format(entry))


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

    def register_fatal_error_function(self, callback=None):
        """ Registers a function to call if a fatal error is caused
            such as a failure to roll back a transaction in case of
            a DB error. The application should always exit.
            The function takes the following arguments:
                1. A message
        """
        self._fatal_error_fn = callback

    def call_fatal_error_function(self, message):
        """ Call the fatal error function. """
        if self._fatal_error_fn:
            self._fatal_error_fn(message)
        else:
            print("Exiting due to fatal error: {}".format(message))

        sys.exit(-1)

    def get_directory(self):
        """ Return the PIM directory. """
        return self._directory

    def get_data_directories(self):
        """ Return a search path of supplied data directories, ie templates, etc. """
        dirs = (
            os.path.join(self._directory, "data"),
            #platform.get_user_data_dir("mrbavii-mypim"),
            os.path.join(os.path.dirname(__file__), "..", "data")
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

    def _perform_rollback(self):
        """ Execute a rollback on the database, die if the command failed. """
        try:
            self._db.execute("ROLLBACK;")
        except Exception as e:
            # Fatal if rollback fails.  To prevent/minimize corruption, exit
            try:
                # Rollback failed, aborting so still clean up
                for fn in self._transaction_cleanup_fns:
                    fn()
            finally:
                self.call_fatal_error_function(str(e))
                sys.exit(-1)

        # Rollback successfull, cleanup
        for fn in self._transaction_cleanup_fns:
            fn()

    def abort_transaction(self):
        """ Set the error flag so the transaction is rolled back instead of commited. """
        self._error_in_transaction = True

    def register_transaction_cleanup_function(self, fn):
        """ Regsiter a function to be called in case a transaction is rolled back. """
        self._transaction_cleanup_fns.append(fn)
    
    def __enter__(self):
        """ Begin a transaction, support nested context calls. """

        if self._transaction_level == 0:
            # Just now starting transaction
            self._error_in_transaction = False
            self._transaction_cleanup_fns = []
            self._db.execute("BEGIN IMMEDIATE;")
        
        self._transaction_level += 1
        return self._db.cursor()

    def __exit__(self, type, value, traceback):
        """ Commit or rollback on leaving the context. """

        if type is not None:
            self._error_in_transaction = True

        try:
            if self._transaction_level == 1:
                # Commit the transaction
                if not self._error_in_transaction:
                    try:
                        self._db.execute("COMMIT;")
                        self._transaction_cleanup_fns = []
                    except:
                        self._perform_rollback()
                        raise
                else:
                    self._perform_rollback()
        finally:
            if self._transaction_level > 0: # In call __enter__ failed before incrementing
                self._transaction_level -= 1
        # If an exception was passed in, reraise it

    def connect(self):
        """ Establish the initial connection to the PIM. """
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

        # We require model_versions before anything else
        with self as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS model_versions(
                    name TEXT UNIQUE,
                    version INTEGER
                );
                """
            )
            cursor.close()

    def check_install(self):
        """ Check if installation is o. """
        for model in self._models:
            if self._models[model].check_install():
                return True

        return False

    def install(self):
        """ Run the installers. """
        for model in self._models:
            if self._models[model].check_install():
                self._models[model].install()

    def open(self):
        """ Open the PIM """
        for model in self._models:
            self._models[model].open()

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
        with self as cursor:
            cursor.execute(
                """
                SELECT version FROM model_versions WHERE name=?;
                """,
                (name,)
            )

            row = cursor.fetchone()
            if row:
                return row["version"]

        return None

    def set_model_version(self, name, version):
        """ Set a model version. """
        with self as cursor:
            if version is None:
                cursor.execute(
                    """
                    DELETE FROM
                        model_versions
                    WHERE
                        name=?;
                    """,
                    (name,)
                )
            else:
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO
                        model_versions (name, version)
                    VALUES
                        (?, ?);
                    """,
                    (name, int(version))
                )

class PimApp(app.App):
    """ A base application object for the PIM. """

    @property
    def appname(self):
        return "mrbavii-mypim"

    @property
    def displayname(self):
        return "MrBAVII MyPIM"

    @property
    def description(self):
        return "A personal information manager"

    def main(self):
        """ Run the application. """

        # Commandline arguments first
        parser = argparse.ArgumentParser(description=self.description)

        parser.add_argument("-e", "--entry", dest="entry", default=None,
            help="Specify an entry point to call. Use '--' to separate the arguments to the entry point")
        parser.add_argument("-l", "--listentry", dest="listentry", default=False,
            action="store_true", help="List entry points")
        parser.add_argument("-p", "--pim", default=None,
            help="Specify the location of the PIM,");

        # -- is used to separate main arguments from subarguments
        argv = sys.argv[1:]
        if "--" in argv:
            pos = argv.index("--")
            self._cmdline = parser.parse_args(argv[:pos])
            self.cmdline.params = argv[pos + 1:]
        else:
            self._cmdline = parser.parse_args(argv)
            self.cmdline.params = []

        # If an entry point is specified, we run in command line only mode
        if self.cmdline.entry or self.cmdline.listentry:
            return self.main_with_entry()
        else:
            return self.gui_main()

    def main_with_entry(self):
        """ Handle calling the entry point. """

        # The main purpose of entry points is if there is any exported data
        # the entry point can be used to process the data without actually
        # loading/connecting to the PIM the data was exported from and
        # without launching in GUI so they can be used from the command line.

        cmdline = self.cmdline

        # If a PIM object was specified, then we load it
        if cmdline.pim:
            pim = Pim(self, cmdline.pim)
            pim.connect()

            if pim.check_install():
                pim.install() # TODO: prompt user first
            pim.open()
        else:
            pim = Pim(self, None) # An empty/unconnected PIM

        if cmdline.listentry:
            for entry in pim.get_model_entries():
                print(entry)
        elif cmdline.entry:
            pim.call_model_entry(cmdline.entry, cmdline.params)

