import shlex
from functools import update_wrapper
from typing import Any

import click
import inject
import pytest
from click.testing import CliRunner


# Tests Fixtures


# Services


class FileSystem:

    def __repr__(self):
        return self.__class__.__name__


class TemplateEngine:

    def __repr__(self):
        return self.__class__.__name__


class services:

    SERVICES = dict(
        filesystem=FileSystem(),
        template_engine=TemplateEngine(),
    )

    def __init__(self, *services):
        self._services = {i: j for i, j in self.SERVICES.items() if i in services}

    def __call__(self, f, *args, **kwargs):
        def new_func(*args, **kwargs):
            ctx = click.get_current_context()
            ctx.__dict__.update(self._services)
            return f(ctx, *args, **kwargs)

        return update_wrapper(new_func, f)

    def __getattr__(self, name: str) -> Any:
        return self._services[name]


# Commands


@click.group(name="test")
def main():
    def config(binder):
        binder.bind(FileSystem, services.SERVICES["filesystem"])
        binder.bind(TemplateEngine, services.SERVICES["template_engine"])

    inject.configure(config, once=True)


@main.command()
@services("filesystem", "template_engine")
def first(ctx):
    click.echo("""test.first""")
    click.echo(f"{ctx.filesystem}")
    click.echo(f"{ctx.template_engine}")


@main.command("inject")
@inject.autoparams()
def inject_function(filesystem: FileSystem, template_engine: TemplateEngine):
    click.echo("""test.second""")
    click.echo(filesystem)
    click.echo(template_engine)


class MyRunner:
    def __init__(self):
        self.__cli_runner = CliRunner(mix_stderr=False)

    def run(self, command):
        from zz import __main__

        result = self.__cli_runner.invoke(__main__.main, shlex.split(command))
        return result

    def test(self, command, stdout="", stderr="", exit_code=0):
        result = self.run(command)
        if result.exception is not None:
            raise result.exception
        self.assert_text(result.stdout, stdout)
        self.assert_text(result.stderr, stderr)
        assert (
            result.exit_code == exit_code
        ), f"Exit code differs {result.exit_code} != {exit_code}"
        return result

    @staticmethod
    def assert_text(obtained, expected):
        import difflib
        from textwrap import dedent

        expected = dedent(expected.lstrip("\n"))
        if obtained != expected:
            obtained = obtained.split("\n")
            expected = expected.split("\n")
            diff = "\n".join(difflib.unified_diff(obtained, expected))
            raise AssertionError(diff)


@pytest.fixture
def runner() -> MyRunner:
    """Fixture for invoking command-line interfaces."""
    return MyRunner()


# Tests


def test_test1(runner):
    runner.test(
        "test first",
        """
        test.first
        FileSystem
        TemplateEngine
        """,
    )


def test_test2(runner):
    runner.test(
        "test inject",
        """
        test.second
        FileSystem
        TemplateEngine
        """,
    )
