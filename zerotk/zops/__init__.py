# -*- coding: utf-8 -*-


def setenv(name, value):
    import os
    import click
    os.environ[name] = value
    click.echo('{}: {}'.format(name, os.environ[name]))


def add_pythonpath(value):
    import sys
    import os
    import click
    value = os.path.normpath(value)
    sys.path.append(value)
    click.echo('SYS.PATH: {}'.format(value))


def call_main(main_func, *argv):
    import sys
    old_argv = sys.argv
    sys.argv = [''] + list(argv)
    try:
        return main_func()
    finally:
        sys.argv = old_argv


def ensure_dir(path):
    import click
    import os
    click.echo('DIRECTORY: {}'.format(path))
    os.makedirs(path, exist_ok=True)


class Console(object):

    TITLE_COLOR = 'yellow'
    EXECUTION_COLOR = 'green'
    OUTPUT_COLOR = 'white'

    @classmethod
    def title(cls, *args):
        cls._secho(['#'] + list(args), cls.TITLE_COLOR)

    @classmethod
    def execution(cls, *args):
        cls._secho(['$'] + list(args), cls.EXECUTION_COLOR)

    @classmethod
    def output(cls, *args):
        cls._secho(args, cls.OUTPUT_COLOR)

    @classmethod
    def _secho(cls, args, fg, join_char=' '):
        import click
        message = join_char.join(args)
        click.secho(message, fg=fg)
