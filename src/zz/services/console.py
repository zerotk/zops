import functools


# def setenv(name, value):
#     import os
#     os.environ[name] = value
#     Console.setting('{}={}'.format(name, os.environ[name]))
#
#
# def add_pythonpath(value):
#     import sys
#     import os
#     value = os.path.normpath(value)
#     sys.path.insert(0, value)
#     Console.setting('SYS.PATH={}'.format(value))
#
#
# def call_main(main_func, *argv):
#     import sys
#     old_argv = sys.argv
#     sys.argv = [''] + list(argv)
#     try:
#         return main_func()
#     except SystemExit as e:
#         return e.code
#     finally:
#         sys.argv = old_argv
#
#
# def ensure_dir(path):
#     import os
#     os.makedirs(path, exist_ok=True)
#     Console.setting('DIRECTORY: {}'.format(path))


class Console(object):

    TITLE_COLOR = "yellow"
    EXECUTION_COLOR = "green"
    SETTING_COLOR = "blue"
    OUTPUT_COLOR = "white"
    INFO_COLOR = "white"
    DEBUG_COLOR = "red"

    SEPARATOR_CHAR = " "
    INDENTATION_TEXT = "  "

    ITEM_PREFIX = "*"
    TITLE_PREFIX = "#"
    DEBUG_PREFIX = "***"
    INFO_PREFIX = "\U0001F6C8"

    @classmethod
    @functools.cache
    def singleton(cls) -> "Console":
        return cls()

    def __init__(self, verbose_level: int = 0):
        self._verbose_level = verbose_level

    def title(self, message: str, indent: int = 0, title_level: int = 1, verbosity: int = 0):
        prefix = self._prefix(self.TITLE_PREFIX * title_level, indent=indent)
        self.secho(prefix + message, fg=self.TITLE_COLOR, verbosity=verbosity)

    #     def execution(self, message, verbose=0):
    #         self._secho(['$'] + [message], self.EXECUTION_COLOR)
    #
    #     def setting(self, message, verbose=0):
    #         self._secho(['!'] + list(args), self.SETTING_COLOR)

    def item(self, message: str, indent: int = 0, fg=OUTPUT_COLOR, verbosity: int = 0):
        prefix = self._prefix(self.ITEM_PREFIX, indent=indent)
        self.secho(prefix + str(message), fg=fg, verbosity=verbosity)

    #     def output(self, *args):
    #         self._secho(args, self.OUTPUT_COLOR)
    #
    #     def response(self, *args):
    #         self._secho(['>'] + list(args), self.OUTPUT_COLOR)

    def info(self, message: str, indent: int = 0, verbosity: int = 0):
        prefix = self._prefix(self.INFO_PREFIX, indent=indent)
        self.secho(prefix + message, self.INFO_COLOR)

    def debug(self, message: str, indent: int = 0, verbosity: int = 0):
        prefix = self._prefix(self.DEBUG_PREFIX, indent=indent)
        self.secho(prefix + message, fg=self.DEBUG_COLOR, verbosity=verbosity)

    def _prefix(
        self, prefix: str, indent: int = 0, separator: str = SEPARATOR_CHAR
    ) -> str:
        return self.INDENTATION_TEXT * indent + prefix + separator

    def secho(self, message: str, fg=OUTPUT_COLOR, verbosity: int = 0) -> None:
        import click

        if self._verbose_level < verbosity:
            return

        message.rstrip("\n")

        click.secho(message, fg=fg)
