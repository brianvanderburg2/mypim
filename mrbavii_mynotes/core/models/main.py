""" The 'main' module is a helper for other modules and also provides the
    tree structure tables.  """

__author__      =   "Brian Allen Vanderburg II"
__copyright__   =   "Copyright (C) 2018 Brian Allen Vanderburg II"
__license__     =   "Apache License 2.0"


from .model import Model, ModelInstaller

class MainModel(Model):
    """ Represent the main model. """
    MODEL_NAME = "main"
    MODEL_VERSION = 1

    def __init__(self, db):
        """ Initialize the model. """
        Model.__init__(self, db)

    def install(self):
        """ Perform installation. """
        return MainModelInstaller(self).install()

    # Settings
        
    def get_setting(self, name):
        """ Get a setting. """
        with self._db as cursor:
            sql = "SELECT value FROM settings WHERE name=?;"
            cursor.execute(sql, (name,))

            row = cursor.fetchone()
            if row:
                return row["value"]

        return None

    def set_setting(self, name, value):
        """ Set a setting. """
        with self._db as cursor:
            if value is None:

                sql = "DELETE FROM settings WHERE name=?"
                cursor.execute(sql, (name,))
            else:
                sql = """
                    INSERT OR REPLACE INTO settings (name, value)
                    VALUES (?, ?);
                """

                cursor.execute(sql, (name, value))

    # Notes

    def create_note(self, parent, position, name):
        """ Create a new note. """
        with self._db as cursor:
            sql = "INSERT INTO notes (parent, position, name) VALUES (?, ?, ?)"
            cursor.execute(sql, (parent, int(position), str(name)))
            return cursor.lastrowid

    def update_note(self, id, position=None, name=None, contents=None):
        """ Update the note. """
        updates = []
        data = {"id": id}

        if name is not None:
            updates.append("name=:name")
            data["name"] = str(name)

        if position is not None:
            updates.append("position=:position")
            data["position"] = int(position)

        if contents is not None:
            updates.append("contents=:contents")
            data["contents"] = contents

        if not updates:
            return

        with self._db as cursor:
            sql = "UPDATE notes SET {0} WHERE id=:id".format(
                ",".join(updates)
            )
            cursor.execute(sql, data)

    def delete_note(self, id):
        """ Delete an item. """
        with self._db as cursor:
            sql = "DELETE FROM notes WHERE id=?"
            cursor.execute(sql, (id,))

    def get_note_children(self, parent=None):
        """ Get all children of an note. """
        with self._db as cursor:
            sql = """\
                SELECT id, position, name FROM notes
                WHERE parent=?
                ORDER BY position
            """
            cursor.execute(sql, (parent,))

            return [dict(row) for row in cursor]

    def move_note(self, id, parent, position):
        """ Move a note to a new parent. """
        # TODO: make sure no cycles
        pass


class MainModelInstaller(ModelInstaller):
    """ Handle install/upgrades for the main model. """

    def install_tables(self):
        """ Perform install. """
        with self._db as cursor:
            sql = []

            sql.append(
                """
                CREATE TABLE IF NOT EXISTS settings(
                    name TEXT UNIQUE,
                    value TEXT
                );
                """
            )
            
            sql.append(
                """
                CREATE TABLE notes (
                    id INTEGER PRIMARY KEY NOT NULL,
                    parent INTEGER REFERENCES notes ( id ),
                    position INTEGER,
                    name TEXT,
                    template TEXT,
                    contents TEXT
                );
                """
            )

            for i in sql:
                cursor.execute(i)

            
            # Set the model version
            self.set_version(1)


    _install_map = {
        None: install_tables
    }

# Specify the models to the loader
MODELS = [MainModel]

