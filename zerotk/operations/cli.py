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
@click.option('--update', default=False, help='Updates all libraries versions.')
def compile(update):
    """
    Update requirements
    """
    from glob import glob

    def get_input_filenames(filename):
        import os

        result = []
        include_lines = [i for i in open(filename, 'r').readlines() if i.startswith('#!INCLUDE')]
        for i_line in include_lines:
            included_filename = i_line.split(' ', 1)[-1].strip()
            included_filename = os.path.join(os.path.dirname(filename), included_filename)
            result.append(included_filename)
        result.append(filename)
        return result

    def get_output_filename(filename):
        import os
        return os.path.splitext(filename)[0] + '.txt'

    base_params = ['--no-index', '-r']
    if update:
        base_params += ['-U']

    for i_filename in glob('requirements/*.in'):
        output_filename = get_output_filename(i_filename)
        input_filenames = get_input_filenames(i_filename)
        click.echo('{}: generating from {}'.format(output_filename, ', '.join(input_filenames)))

        params = base_params + input_filenames + ['-o', output_filename]
        click.echo('$ pip-compile {}'.format(' '.join(params)))
        _pip_compile(*params)


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
