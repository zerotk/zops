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
