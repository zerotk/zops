from __future__ import unicode_literals

import pytest

from zerotk.clikit.command import Command
from zerotk.clikit.command import InvalidFixture
from zerotk.clikit.console import BufferedConsole
from zerotk.text import dedent


# ===================================================================================================
# TESTS
# ===================================================================================================


class Test:

    def testConstructor(self):
        def Hello():
            """
            Hello function.
            """

        cmd = Command(Hello)
        assert cmd.names == ["Hello"]
        assert cmd.description == "Hello function."

        cmd = Command(Hello, names="h")
        assert cmd.names == ["h"]

        cmd = Command(Hello, names=["h1", "h2"])
        assert cmd.names == ["h1", "h2"]

        def no_doc():
            """"""

        cmd = Command(no_doc)
        assert cmd.description == "(no description)"

    def testArg(self):

        arg = Command.Arg("arg", "INVALID_ARG_TYPE")

        with pytest.raises(TypeError):
            arg.ConfigureArgumentParser(None)

    def testArguments(self):

        def Hello(
            console_, filename, option="yes", no_setup=False, no_default=None, *config
        ):
            """
            Hello function.

            This is Hello.

            :param filename: The name of the file.
            :param no_setup: False if set
            :param no_default: Receives None
            :param config: Configurations
            """
            console_.Print("%s - %s" % (filename, option))
            [console_.Item(i) for i in config]

        cmd = Command(Hello)
        assert cmd.names == ["Hello"]
        assert cmd.description == "Hello function."

        assert cmd.args.keys() == [
            "console_",
            "filename",
            "option",
            "no_setup",
            "no_default",
            "config",
        ]
        assert map(unicode, cmd.args.values()) == [
            "console_",
            "filename",
            "option=yes",
            "no-setup",
            "no-default=VALUE",
            "*config",
        ]
        assert map(repr, cmd.args.values()) == [
            "<Arg console_>",
            "<Arg filename>",
            "<Arg option=yes>",
            "<Arg no-setup>",
            "<Arg no-default=VALUE>",
            "<Arg *config>",
        ]
        assert cmd.kwargs is None

        console = BufferedConsole()
        cmd.Call(
            fixtures={"console_": (lambda: console, lambda: None)},
            argd={"filename": "alpha.txt", "config": ["one", "two", "three"]},
        )
        assert console.GetOutput() == "alpha.txt - yes\n- one\n- two\n- three\n"

        # Ignores all invalid arguments passed to Call.
        console = BufferedConsole()
        cmd.Call(
            fixtures={"console_": (lambda: console, lambda: None)},
            argd={"filename": "bravo.txt", "INVALID": "INVALID"},
        )
        assert console.GetOutput() == "bravo.txt - yes\n"

        with pytest.raises(InvalidFixture):
            cmd.Call({}, {"filename": "alpha.txt"})

        with pytest.raises(TypeError):
            cmd.Call({"console_": console}, {})

        assert cmd.description == "Hello function."
        assert cmd.long_description == dedent(
            """
            Hello function.

            This is Hello.
            """
        )

        assert cmd.FormatHelp() == dedent(
            """
            Usage:
                Hello <filename> <*config> [--option=yes],[--no-setup],[--no-default=VALUE]

            Parameters:
                filename   The name of the file.
                config   Configurations

            Options:
                --option   (no description) [default: yes]
                --no-setup   False if set
                --no-default   Receives None

            """
        )

        assert cmd.FormatHelp() == dedent(
            """
            Usage:
                Hello <filename> <*config> [--option=yes],[--no-setup],[--no-default=VALUE]

            Parameters:
                filename   The name of the file.
                config   Configurations

            Options:
                --option   (no description) [default: yes]
                --no-setup   False if set
                --no-default   Receives None

            """
        )

        import argparse

        parser = argparse.ArgumentParser("TEST")
        cmd.ConfigureArgumentParser(parser)
        assert parser.format_help() == dedent(
            """
            usage: TEST [-h] [--option OPTION] [--no-setup] [--no-default NO_DEFAULT]
                        filename [config [config ...]]

            positional arguments:
              filename
              config

            optional arguments:
              -h, --help            show this help message and exit
              --option OPTION
              --no-setup
              --no-default NO_DEFAULT

            """
        )

    def testNoArgument(self):

        def Hello():
            """
            Hello function.

            :param noargument: This argument does not exist.
            """

        with pytest.raises(RuntimeError):
            Command(Hello)

    def testDEFAULT(self):
        """
        Tests the DEFAULT argument type to declare a positional argument with a default value.
        """

        def Hello(console_, first=Command.DEFAULT("one")):
            """
            Hello function.
            """
            console_.Print(first)

        cmd = Command(Hello)
        assert cmd.names == ["Hello"]
        assert cmd.description == "Hello function."

        assert cmd.args.keys() == ["console_", "first"]
        assert map(unicode, cmd.args.values()) == ["console_", "first=one"]
        assert cmd.kwargs is None

        console = BufferedConsole()
        cmd.Call(fixtures={"console_": (lambda: console, lambda: None)}, argd={})
        assert console.GetOutput() == "one\n"

        console = BufferedConsole()
        cmd.Call(
            fixtures={"console_": (lambda: console, lambda: None)},
            argd={"first": "two"},
        )
        assert console.GetOutput() == "two\n"
