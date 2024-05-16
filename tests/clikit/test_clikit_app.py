from __future__ import unicode_literals

import inspect
import sys

import pytest
import six
from mock import Mock

from zerotk.clikit.app import App
from zerotk.clikit.app import UnknownApp
from zerotk.clikit.console import BufferedConsole
from zerotk.clikit.console import Console
from zerotk.text import dedent


# ===================================================================================================
# TESTS
# ===================================================================================================


class Test:
    """
    Tests for App class using py.test
    """

    def _TestMain(self, app, args, output, retcode=App.RETCODE_OK):
        assert app.Main(args.split()) == retcode
        assert app.console.GetOutput() == output

    def testSysArgv(self):
        def Case(console_, argv_, first, second):
            console_.Print("%s..%s" % (first, second))
            console_.Print(argv_)

        app = App("test", color=False, buffered_console=True)
        app.Add(Case)

        old_sys_argv = sys.argv
        sys.argv = [sys.argv[0], "case", "alpha", "bravo"]
        try:
            app.Main()
            assert app.console.GetOutput() == "alpha..bravo\ncase\nalpha\nbravo\n"
        finally:
            sys.argv = old_sys_argv

    def testBufferedConsole(self):
        app = App("test", color=False, buffered_console=True)
        assert type(app.console) == BufferedConsole

        app = App("test", color=False)
        assert type(app.console) == Console

    def testHelp(self):

        def TestCmd(console_, first, second, option=1, option_no=False):
            """
            This is a test.

            :param first: This is the first parameter.
            :param second: This is the second and last parameter.
            :param option: This must be a number.
            :param option_no: If set, says nop.
            """

        app = App("test", color=False, buffered_console=True)
        app.Add(TestCmd)

        self._TestMain(
            app,
            "",
            dedent(
                """

            Usage:
                test <subcommand> [options]

            Commands:
                test-cmd   This is a test.

            """
            ),
        )

        self._TestMain(
            app,
            "--help",
            dedent(
                """

            Usage:
                test <subcommand> [options]

            Commands:
                test-cmd   This is a test.

            """
            ),
        )

        self._TestMain(
            app,
            "test-cmd --help",
            dedent(
                """
                    This is a test.

                    Usage:
                        test-cmd <first> <second> [--option=1],[--option-no]

                    Parameters:
                        first   This is the first parameter.
                        second   This is the second and last parameter.

                    Options:
                        --option   This must be a number. [default: 1]
                        --option-no   If set, says nop.


                """
            ),
        )

        self._TestMain(
            app,
            "test-cmd",
            dedent(
                """
                    ERROR: Too few arguments.

                    This is a test.

                    Usage:
                        test-cmd <first> <second> [--option=1],[--option-no]

                    Parameters:
                        first   This is the first parameter.
                        second   This is the second and last parameter.

                    Options:
                        --option   This must be a number. [default: 1]
                        --option-no   If set, says nop.


                """
            ),
            app.RETCODE_ERROR,
        )

    def testApp(self):
        """
        Tests App usage and features.
        """

        def Case1(console_):
            """
            A "hello" message from case 1
            """
            console_.Print("Hello from case 1")

        def Case2(console_):
            """
            A "hello" message from case 2

            Additional help for this function is available.
            """
            console_.Print("Hello from case 2")

        def Case3(console_):
            console_.Print("Hello from case 3")

        def Case4(console_):
            console_.Print("Hello from case 4 (AKA: four)")

        app = App("test", color=False, buffered_console=True)
        app.Add(Case1, alias="cs")
        app.Add(Case2)
        case3_cmd = app.Add(Case3, alias=("c3", "cs3"))
        app.Add(Case4, name="four")

        # Test duplicate name
        with pytest.raises(ValueError):
            app.Add(case3_cmd.func, alias="cs")

        # Test commands listing
        assert app.ListAllCommandNames() == [
            "case1",
            "cs",
            "case2",
            "case3",
            "c3",
            "cs3",
            "four",
        ]

        # Tests all commands output
        self._TestMain(app, "case1", "Hello from case 1\n")
        self._TestMain(app, "cs", "Hello from case 1\n")
        self._TestMain(app, "case2", "Hello from case 2\n")
        self._TestMain(app, "case3", "Hello from case 3\n")
        self._TestMain(app, "c3", "Hello from case 3\n")
        self._TestMain(app, "cs3", "Hello from case 3\n")
        self._TestMain(app, "four", "Hello from case 4 (AKA: four)\n")

        # Tests output when an invalid command is requested
        self._TestMain(
            app,
            "INVALID",
            dedent(
                """
            ERROR: Unknown command u'INVALID'

            Usage:
                test <subcommand> [options]

            Commands:
                case1, cs        A "hello" message from case 1
                case2            A "hello" message from case 2
                case3, c3, cs3   (no description)
                four             (no description)

            """
            ),
            app.RETCODE_ERROR,
        )

    def testConf(self, tmpdir):
        """
        Tests the configuration plugin (ConfPlugin)
        """
        conf_filename = tmpdir.join("ConfigurationCmd.conf")

        app = App(
            "test",
            color=False,
            conf_defaults={
                "group": {
                    "value": "ALPHA",
                }
            },
            conf_filename=six.text_type(conf_filename),
            buffered_console=True,
        )

        def ConfigurationCmd(console_, conf_):
            """
            Test Set/Get methods from configuration object.
            """
            console_.Print("conf_.filename: %s" % conf_.filename)
            console_.Print("group.value: %s" % conf_.Get("group", "value"))

            conf_.Set("group", "value", "BRAVO")
            console_.Print("group.value: %s" % conf_.Get("group", "value"))

            assert not conf_filename.check(file=1)
            conf_.Save()
            assert conf_filename.check(file=1)

        app.Add(ConfigurationCmd)

        self._TestMain(
            app,
            "configuration-cmd",
            "conf_.filename: %s\ngroup.value: ALPHA\ngroup.value: BRAVO\n"
            % conf_filename,
        )

        # Creating an application with an existing configuration file.
        assert conf_filename.check(file=1)
        app = App(
            "test",
            color=False,
            conf_defaults={
                "group": {
                    "value": "ALPHA",
                }
            },
            conf_filename=six.text_type(conf_filename),
            buffered_console=True,
        )

        def Cmd(console_, conf_):
            console_.Print(conf_.filename)
            console_.Print(conf_.Get("group", "value"))

        app.Add(Cmd)

        self._TestMain(app, "cmd", "%s\nBRAVO\n" % conf_filename)

    def testPositionalArgs(self):
        """
        >test command alpha bravo
        alpha..bravo
        """
        app = App("test", color=False, buffered_console=True)

        def Command(console_, first, second):
            console_.Print("%s..%s" % (first, second))

        app.Add(Command)

        app.TestScript(inspect.getdoc(self.testPositionalArgs))

    def testConsolePluginVerbosity(self):
        """
        >test command
        quiet
        normal
        >test command --verbose
        quiet
        normal
        verbose
        >test command --quiet
        quiet
        """
        app = App("test", color=False, buffered_console=True)

        def Command(console_):
            console_.PrintQuiet("quiet")
            console_.Print("normal")
            console_.PrintVerbose("verbose")

        app.Add(Command)

        app.TestScript(inspect.getdoc(self.testConsolePluginVerbosity))

    def testConsolePluginNoColor(self):
        """
        >test command
        console.color = False
        >test command --no-color
        console.color = False
        """
        app = App("test", color=False, buffered_console=True)

        def Command(console_):
            console_.Print("console.color = %s" % console_.color)

        app.Add(Command)

        app.TestScript(inspect.getdoc(self.testConsolePluginNoColor))

    def testPositionalArgsWithDefaults(self):
        """
        >test hello
        NOTHING

        >test hello something
        something
        """
        app = App("test", color=False, buffered_console=True)

        def Hello(console_, message=App.DEFAULT("NOTHING")):
            console_.Print(message)

        app.Add(Hello)

        app.TestScript(inspect.getdoc(self.testPositionalArgsWithDefaults))

    def testOptionArgs(self):
        """
        >test command
        1..2
        >test command --first=alpha --second=bravo
        alpha..bravo
        """
        app = App("test", color=False, buffered_console=True)

        def Command(console_, first="1", second="2"):
            console_.Print("%s..%s" % (first, second))

        app.Add(Command)

        app.TestScript(inspect.getdoc(self.testOptionArgs))

    def testOptionUnderscore(self):
        """
        >test command
        my_option = default
        >test command --my-option=custom
        my_option = custom
        """
        app = App("test", color=False, buffered_console=True)

        def Command(console_, my_option="default"):
            console_.Print("my_option = " + my_option)

        app.Add(Command)

        app.TestScript(inspect.getdoc(self.testOptionUnderscore))

    def testUnknownOptionArgs(self):

        def Command(console_):
            """"""

        app = App("test", color=False, buffered_console=True)
        app.Add(Command)

        app.TestScript(
            dedent(
                """
            >test command --foo --bar [retcode=1]
            ERROR: Unrecognized arguments: --foo --bar

            (no description)

            Usage:
                command\s\s

            Parameters:

            Options:
            """.replace(
                    "\s", " "
                )
            )
        )

    def testBoolArgFalse(self):
        """
        >test command
        False
        >test command --option
        True
        """
        app = App("test", color=False, buffered_console=True)

        def Command(console_, option=False):
            console_.Print(option)

        app.Add(Command)
        app.TestScript(inspect.getdoc(self.testBoolArgFalse))

    def testBoolArgTrue(self):

        def Command(console_, option=True):
            """"""

        # We cannot have a command with boolean default True
        app = App("test", color=False, buffered_console=True)
        with pytest.raises(RuntimeError) as e:
            app.Add(Command)

        assert (
            six.text_type(e.value)
            == "Clikit commands are not allowed to have boolean parameters that default to True."
        )

    def testColor(self):
        app = App("test", color=True, buffered_console=True)

        assert app.console.color == True

        def Case():
            """
            This is Case.
            """

        app.Add(Case)

        self._TestMain(
            app,
            "",
            dedent(
                """

                    Usage:
                        test <subcommand> [options]

                    Commands:
                        %(teal)scase%(reset)s   This is Case.

                """
                % Console.COLOR_CODES
            ),
        )

    def testColorama(self):
        """
        Importing colorama from inside pytest USED TO raise an exception:

            File "D:\Kaniabi\EDEn\dist\12.0-all\colorama-0.2.5\lib\site-packages\colorama\win32.py", line 64
            in GetConsoleScreenBufferInfo
            >           handle, byref(csbi))
            E       ArgumentError: argument 2: <type 'exceptions.TypeError'>: expected LP_CONSOLE_SCREEN_BUFFER_INFO
                                   instance instead of pointer to CONSOLE_SCREEN_BUFFER_INFO
        """

    def testFixture1(self):

        def MyFix():
            return "This is a custom fixture"

        def Cmd(console_, my_fix_):
            console_.Print(my_fix_)

        app = App("test", color=True, buffered_console=True)
        app.Fixture(MyFix)
        app.Add(Cmd)

        self._TestMain(app, "cmd", "This is a custom fixture\n")

    def testFixture2(self):
        def MyFix():
            return "This is rubles."

        def Cmd(console_, rubles_):
            console_.Print(rubles_)

        app = App("test", color=True, buffered_console=True)
        app.Fixture(MyFix, name="rubles")
        app.Add(Cmd)

        self._TestMain(app, "cmd", "This is rubles.\n")

    def testFixtureWithFinalizer(self):

        finalizer = Mock()

        def MyFix():
            yield "This is rubles."
            finalizer()

        def Cmd(console_, rubles_):
            console_.Print(rubles_)

        app = App("test", color=True, buffered_console=True)
        app.Fixture(MyFix, name="rubles")
        app.Add(Cmd)

        self._TestMain(app, "cmd", "This is rubles.\n")

        finalizer.assert_called_once_with()

    def testExecuteCommand(self):

        def Cmd(console_, subject="World"):
            console_.Print("Hello, %s!" % subject)

        app = App("test", color=False, buffered_console=True)
        app.Add(Cmd)

        retcode, output = app.ExecuteCommand("cmd")
        assert retcode == app.RETCODE_OK
        assert output == "Hello, World!\n"

        retcode, output = app.ExecuteCommand("cmd", "Alpha")
        assert retcode == app.RETCODE_OK
        assert output == "Hello, Alpha!\n"

    def testCommandDecorator(self):

        app = App("test", color=False, buffered_console=True)

        @app
        def Alpha(console_):
            console_.Print("Alpha")

        @app()
        def Bravo(console_):
            console_.Print("Bravo")

        assert app.ExecuteCommand("alpha") == (app.RETCODE_OK, "Alpha\n")
        assert app.ExecuteCommand("bravo") == (app.RETCODE_OK, "Bravo\n")

    def testFixtureDecorator(self):

        app = App("test", color=False, buffered_console=True)

        @app.Fixture
        def Alpha():
            return "alpha"

        @app.Fixture()
        def Bravo():
            return "bravo"

        def Command(console_, alpha_, bravo_):
            console_.Print("The names are: %(alpha_)s and %(bravo_)s." % locals())

        app.Add(Command)

        self._TestMain(
            app,
            "command",
            dedent(
                """
                    The names are: alpha and bravo.

                """
            ),
        )

    def testUnknownApp(self):
        app = App("test", color=False, buffered_console=True)

        with pytest.raises(UnknownApp):
            app.TestCall("UNKNOWN")
