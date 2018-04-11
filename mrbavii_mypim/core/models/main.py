""" The 'main' module is a helper for other modules.  """

__author__      =   "Brian Allen Vanderburg II"
__copyright__   =   "Copyright (C) 2018 Brian Allen Vanderburg II"
__license__     =   "Apache License 2.0"


from .model import Model, ModelInstaller

class MainModel(Model):
    """ Represent the main model. """
    MODEL_NAME="main"
    MODEL_VERSION=1

    def __init__(self, pim):
        Model.__init__(self, pim)


    def install(self):
        return MainModelInstaller(self).install()
        
    def get_pim_setting(self, name):
        """ Get a PIM setting. """
        with self._pim as cursor:
            cursor.execute(
                """
                SELECT value FROM pim_settings WHERE name=?;
                """,
                (name,)
            )

            row = cursor.fetchone()
            if row:
                return row["value"]

        return None

    def set_pim_setting(self, name, value):
        """ Set a PIM setting. """
        with self as cursor:
            if value is None:
                cursor.execute(
                    """
                    DELETE FROM
                        pim_settings
                    WHERE
                        name=?;
                    """,
                    (name,)
                )
                self._pim_settings.pop(name, None)
            else:
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO
                        pim_settings (name, value)
                    VALUES
                        (?, ?);
                    """,
                    (name, value)
                )
                self._pim_settings[name] = value


class MainModelInstaller(ModelInstaller):
    """ Handle install/upgrades for the main model. """

    def install_tables(self):
        with self._pim as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS pim_settings(
                    name TEXT UNIQUE,
                    value TEXT
                );
                """
            )
            
            self.set_version(1)


    _install_map = {
        None: install_tables
    }

# Specify the models to the loader
MODELS = [MainModel]

