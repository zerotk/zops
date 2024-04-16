from __future__ import unicode_literals

import os
import sys

import mock
from six import StringIO

from zerotk.clikit.console import BufferedConsole, Console


#===================================================================================================
# TESTS
#===================================================================================================

class Test:

    def testConsole(self):
        import pytest

        # Test verbosity control
        with pytest.raises(ValueError):
            Console(verbosity=9)

        oss = StringIO()
        console = Console(verbosity=1, stdout=oss)
        console.PrintQuiet('Alpha.q')
        console.Print('Alpha.n')
        console.PrintVerbose('Alpha.v')
        assert oss.getvalue() == '''Alpha.q\nAlpha.n\n'''

        oss = StringIO()
        console = Console(verbosity=0)
        console.SetStdOut(oss)
        console.PrintQuiet('Alpha.q')
        console.Print('Alpha.n')
        console.PrintVerbose('Alpha.v')
        console.PrintError('Alpha.PrintError')  # For now, stdout and stoerr are the same!
        assert oss.getvalue() == '''Alpha.q\nAlpha.PrintError\n'''

        # Testing use of indent
        oss = StringIO()
        console = Console(verbosity=1, stdout=oss)
        console.Print('Alpha.n\nAlpha.n2')
        assert oss.getvalue() == '''Alpha.n\nAlpha.n2\n'''

        oss = StringIO()
        console = Console(verbosity=1, stdout=oss)
        console.Print('Alpha.n\nAlpha.n2', indent_=1)
        assert oss.getvalue() == '''    Alpha.n\n    Alpha.n2\n'''

        # Behavior should be the same as Indent function
        from zerotk.text import indent
        assert indent('''Alpha.n\nAlpha.n2\n''') == oss.getvalue()

        oss = StringIO()
        console = Console(verbosity=1, stdout=oss)
        console.Print('Alpha.n\n    Alpha.n2', indent_=1)
        assert oss.getvalue() == '''    Alpha.n\n        Alpha.n2\n'''
        assert indent('''Alpha.n\n    Alpha.n2\n''') == oss.getvalue()


        # Test color control
        console = Console(color=None)

        color_codes = dict(
            red='\x1b[31;01m',
            blue='\x1b[34;01m',
            reset='\x1b[39;49;00m',
        )

        # Stacking colors (only the last one will prevail)
        oss = StringIO()
        console = Console(color=True, colorama=False, stdout=oss)
        console.Print('<red>alpha<blue>bravo</></>charlie')
        assert oss.getvalue() == '%(red)salpha%(blue)sbravo%(reset)s%(red)s%(reset)scharlie\n' % color_codes

        # Printing multiple lines... as a string
        oss = StringIO()
        console = Console(stdout=oss)
        console.Print('one\ntwo\nthree')
        assert oss.getvalue() == 'one\ntwo\nthree\n'

        # Printing multiple lines... as a list
        oss = StringIO()
        console = Console(stdout=oss)
        console.Print(['one', 'two', 'three'])
        assert oss.getvalue() == 'one\ntwo\nthree\n'

        # Automatically resets colors when reaching the eol
        oss = StringIO()
        console = Console(color=True, colorama=False, stdout=oss)
        console.Print('<red>alpha')
        assert oss.getvalue() == '%(red)salpha%(reset)s\n' % color_codes

        # Test Progress methods
        oss = StringIO()
        console = Console(verbosity=2, stdout=oss)
        console.Progress('Doing...')
        assert oss.getvalue() == '''Doing...: '''
        console.ProgressOk()
        assert oss.getvalue() == '''Doing...: OK\n'''

        oss = StringIO()
        console = Console(verbosity=2, stdout=oss)
        console.Progress('Doing...')
        assert oss.getvalue() == '''Doing...: '''
        console.ProgressError('Failed!')
        assert oss.getvalue() == '''Doing...: Failed!\n'''

        oss = StringIO()
        console = Console(verbosity=2, stdout=oss)
        console.Progress('Doing...')
        assert oss.getvalue() == '''Doing...: '''
        console.ProgressWarning('Skipped!')
        assert oss.getvalue() == '''Doing...: Skipped!\n'''

        # Test Item
        oss = StringIO()
        console = Console(verbosity=2, stdout=oss)
        console.Item('alpha')
        console.Item('bravo')
        console.Item('charlie')
        assert oss.getvalue() == '''- alpha\n- bravo\n- charlie\n'''

        # Test Ask methods
        iss = StringIO()
        iss.write('alpha\n')
        iss.seek(0)
        console = BufferedConsole(verbosity=2, stdin=iss)
        assert console.Ask('Ask:') == 'alpha'
        assert console.GetOutput() == 'Ask: '

        with mock.patch('getpass.getpass', autospec=True, return_value='MOCK_GETPASS') as mock_getpass:
            iss = StringIO()
            console = BufferedConsole(verbosity=2, stdin=iss)

            # This fails in Eclipse/PyDev because getpass is poorly overwritten.
            assert console.AskPassword() == 'MOCK_GETPASS'
            assert console.GetOutput() == 'Password: '

        mock_getpass.assert_called_once_with(prompt='', stream=iss)


    def testBufferedConsole(self):
        console = BufferedConsole()

        console.Print('alpha')
        assert console.GetOutput() == '''alpha\n'''

        console.Print('bravo')
        assert console.GetOutput() == '''bravo\n'''


    def testAutoColor(self):
        console = Console()
        assert console.color == False

        class FakeStdout:
            '''
            Mocks the sys.stdout.isatty function behavior.
            '''
            def __init__(self):
                self._isatty = False
            def isatty(self):
                return self._isatty

        sys_stdout = sys.stdout
        sys.stdout = FakeStdout()
        try:
            # Tests sys.stdout.isatty attribute
            console.color = None
            assert console.color == False

            # Tests COLORTERM environment variable
            sys.stdout._isatty = True
            assert console.color == False

            os_environ = os.environ
            os.environ = dict(os.environ)
            os.environ['COLORTERM'] = '1'
            try:
                console.color = None
                assert console.color == True
            finally:
                os.environ = os_environ

            # Tests TERM environment variable
            console.color = not console._AutoColor()
            assert console.color == (not console._AutoColor())

            console.color = None
            assert console.color == console._AutoColor()

            os_environ = os.environ
            os.environ = dict(os.environ)
            os.environ['TERM'] = 'color'
            try:
                console.color = None
                assert console.color == True
            finally:
                os.environ = os_environ
        finally:
            sys.stdout = sys_stdout


    def testColorama(self):
        '''
        Smoke test to make sure colorama works from inside pytest. In previous version of pytest
        the colorama import failed if called from inside pytest.
        '''
        oss = StringIO()
        console = Console(color=True, colorama=True, stdout=oss)
        console.Print('Hello')
        assert oss.getvalue() == 'Hello\n'
