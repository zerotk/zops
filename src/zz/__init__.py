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
    except SystemExit as e:
        return e.code
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
    INFO_COLOR = 'white'
    DEBUG_COLOR = 'red'

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
    def item(cls, *args, ident=0):
        prefix = cls._idented('*', ident)
        cls._secho([prefix] + list(args), cls.OUTPUT_COLOR)

    @classmethod
    def output(cls, *args):
        cls._secho(args, cls.OUTPUT_COLOR)

    @classmethod
    def response(cls, *args):
        cls._secho(['>'] + list(args), cls.OUTPUT_COLOR)

    @classmethod
    def info(cls, *args):
        cls._secho(['\U0001F6C8'] + list(args), cls.INFO_COLOR)

    @classmethod
    def debug(cls, *args):
        cls._secho(['***'] + list(args), cls.DEBUG_COLOR)

    @classmethod
    def _idented(cls, text, ident):
        return '  ' * ident + text

    @classmethod
    def _secho(cls, args, fg, join_char=' '):
        import click
        message = join_char.join(args)
        message.rstrip('\n')
        click.secho(message, fg=fg)
