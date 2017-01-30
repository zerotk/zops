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
