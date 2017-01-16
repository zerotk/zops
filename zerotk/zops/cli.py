# -*- coding: utf-8 -*-
import click
import click_plugins
from pkg_resources import iter_entry_points


click.disable_unicode_literals_warning = True


@click_plugins.with_plugins(iter_entry_points('zops.plugins'))
@click.group()
def main():
    pass


if __name__ == '__main__':
    main()
