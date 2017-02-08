# -*- coding: utf-8 -*-


def setenv(name, value):
    import os
    os.environ[name] = value
    Console.setting('{}={}'.format(name, os.environ[name]))


def add_pythonpath(value):
    import sys
    import os
    value = os.path.normpath(value)
    sys.path.insert(0, value)
    Console.setting('SYS.PATH={}'.format(value))


def call_main(main_func, *argv):
    import sys
    old_argv = sys.argv
    sys.argv = [''] + list(argv)
    try:
        return main_func()
    finally:
        sys.argv = old_argv


def ensure_dir(path):
    import os
    os.makedirs(path, exist_ok=True)
    Console.setting('DIRECTORY: {}'.format(path))


class Console(object):

    TITLE_COLOR = 'yellow'
    EXECUTION_COLOR = 'green'
    SETTING_COLOR = 'blue'
    OUTPUT_COLOR = 'white'

    @classmethod
    def title(cls, *args):
        cls._secho(['#'] + list(args), cls.TITLE_COLOR)

    @classmethod
    def execution(cls, *args):
        cls._secho(['$'] + list(args), cls.EXECUTION_COLOR)

    @classmethod
    def setting(cls, *args):
        cls._secho(['!'] + list(args), cls.SETTING_COLOR)

    @classmethod
    def item(cls, *args):
        cls._secho(['*'] + list(args), cls.OUTPUT_COLOR)

    @classmethod
    def output(cls, *args):
        cls._secho(args, cls.OUTPUT_COLOR)

    @classmethod
    def _secho(cls, args, fg, join_char=' '):
        import click
        message = join_char.join(args)
        click.secho(message, fg=fg)
