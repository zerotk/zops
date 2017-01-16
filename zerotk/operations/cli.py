# -*- coding: utf-8 -*-
import click


click.disable_unicode_literals_warning = True


@click.group()
def main():
    pass


@main.group()
def req():
    pass


@req.command()
def update():
    """
    Update requirements
    """
    params = ['--no-index', '-r']
    if update:
        params += ['-U']

    _pip_compile(
        *params + ['requirements/production.in', '-o', 'requirements/production.txt']
    )
    _pip_compile(
        *params + ['requirements/production.in', 'requirements/development.in', '-o', 'requirements/development.txt']
    )


def _pip_compile(*args):
    """
    Performs pip-compile (from piptools) with a twist.

    We force editable requirements to use GIT repository (parameter obtain=True) so we have setuptools_scm working on
    them (axado.runner uses setuptools_scm).
    """
    from contextlib import contextmanager

    @contextmanager
    def replaced_argv(args):
        import sys
        argv = sys.argv
        sys.argv = [''] + list(args)
        yield
        sys.argv = argv

    from pip.req.req_install import InstallRequirement
    try:
        InstallRequirement.update_editable_
    except AttributeError:
        InstallRequirement.update_editable_ = InstallRequirement.update_editable
        InstallRequirement.update_editable = lambda s, _o: InstallRequirement.update_editable_(s, True)

    with replaced_argv(args):
        from piptools.scripts.compile import cli
        try:
            cli()
        except SystemExit as e:
            return e.code


if __name__ == '__main__':
    main()
