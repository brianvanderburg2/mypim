""" App helper """

__author__      =   "Brian Allen Vanderburg II"
__copyright__   =   "Copyright (C) 2017 Brian Allen Vanderburg II"
__license__     =   "Apache License 2.0"


from mrbaviirc.app import AppHelper


class NotesAppHelper(AppHelper):
    """ A base application helper object. """
    # TODO: move this to core/app.py

    @property
    def appname(self):
        return "mrbavii-mynotes"

    @property
    def displayname(self):
        return "MrBAVII MyNotes"

    @property
    def description(self):
        return "A personal notes and information manager."

    def create_arg_parser(self):
        """ Create the command line argument parser. """
        parser = AppHelper.create_arg_parser(self)

        parser.add_argument("-d", "--dir", default=None,
            help="Specify the location of the notes direcotry,");

        return parser

    def main(self):
        """ Run the application. """
        return self.gui_main()



