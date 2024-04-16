# coding: UTF-8
from __future__ import unicode_literals

from zerotk.text import dedent, indent, safe_split, match_any, format_it


def test_dedent0():
    string = dedent('oneline')
    assert string == 'oneline'


def test_dedent1():
    string = dedent(
        """
        oneline
        """
    )
    assert string == 'oneline'


def test_dedent2():
    string = dedent(
        """
        oneline
        twoline
        """
    )
    assert string == 'oneline\ntwoline'


def test_dedent3():
    string = dedent(
        """
        oneline
            tabbed
        """
    )
    assert string == 'oneline\n    tabbed'


def test_dedent4():
    string = dedent(
        """
        oneline
            tabbed
        detabbed
        """
    )
    assert string == 'oneline\n    tabbed\ndetabbed'


def test_dedent5():
    string = dedent(
        """
        oneline
        """,
        ignore_first_linebreak=False
    )
    assert string == '\noneline'


def test_dedent6():
    string = dedent(
        """
        oneline
        """,
        ignore_last_linebreak=False
    )
    assert string == 'oneline\n'


def test_dedent7():
    """
    Test a string that has an 'empty line' with 4 spaces above indent level
    """
    # Using a trick to avoid auto-format to remove the empty spaces.
    string = dedent(
        """
        line
        %s
        other_line
        """ % '    '
    )
    assert string == 'line\n    \nother_line'


def test_dedent8():
    """
    Test not the first line in the right indent.
    """
    string = dedent(
        """
            alpha
          bravo
        charlie
        """
    )
    assert string == '    alpha\n  bravo\ncharlie'


def test_dedent9():
    """
    Test behavior when using \t at the start of a string. .. seealso:: BEN-21 @ JIRA
    """
    string = dedent(
        """
            alpha
        \tbravo
        """
    )
    assert string == '    alpha\n\tbravo'


def test_dedent10():
    """
    Checking how dedent handles empty lines at the end of string without parameters.
    """
    string = dedent(
        """
        alpha
        """
    )
    assert string == 'alpha'
    string = dedent(
        """
        alpha

        """
    )
    assert string == 'alpha\n'
    string = dedent(
        """
        alpha


        """
    )
    assert string == 'alpha\n\n'


def test_dedent11():
    """
    Check calling dedent more than once.
    """
    string = dedent(
        """
        alpha
        bravo
        charlie
        """
    )
    assert string == 'alpha\nbravo\ncharlie'
    string = dedent(string)
    assert string == 'alpha\nbravo\ncharlie'
    string = dedent(string)
    assert string == 'alpha\nbravo\ncharlie'


def test_indent():
    assert indent('') == ''

    assert indent('alpha') == '    alpha'

    assert indent('alpha', indent_=2) == '        alpha'
    assert indent('alpha', indentation='...') == '...alpha'

    # If the original text ended with '\n' the resulting text must also end with '\n'
    assert indent('alpha\n') == '    alpha\n'

    # If the original text ended with '\n\n' the resulting text must also end with '\n\n'
    # Empty lines are not indented.
    assert indent('alpha\n\n') == '    alpha\n\n'

    # Empty lines are not indented nor cleared.
    assert indent('alpha\n  \ncharlie') == '    alpha\n  \n    charlie'

    # Empty lines are not indented nor cleared.
    assert indent(['alpha', 'bravo']) == '    alpha\n    bravo\n'

    # Multi-line test.
    assert indent('alpha\nbravo\ncharlie') == '    alpha\n    bravo\n    charlie'


def test_safe_split():
    assert safe_split('alpha', ' ') == ['alpha']
    assert safe_split('alpha bravo', ' ') == ['alpha', 'bravo']
    assert safe_split('alpha bravo charlie', ' ') == ['alpha', 'bravo', 'charlie']

    assert safe_split('alpha', ' ', 1) == ['alpha', '']
    assert safe_split('alpha bravo', ' ', 1) == ['alpha', 'bravo']
    assert safe_split('alpha bravo charlie', ' ', 1) == ['alpha', 'bravo charlie']

    assert safe_split('alpha', ' ', 1, default=9) == ['alpha', 9]
    assert safe_split('alpha bravo', ' ', 1, default=9) == ['alpha', 'bravo']
    assert safe_split('alpha bravo charlie', ' ', 1, default=9) == ['alpha', 'bravo charlie']

    assert safe_split('alpha', ' ', 2) == ['alpha', '', '']
    assert safe_split('alpha bravo', ' ', 2) == ['alpha', 'bravo', '']
    assert safe_split('alpha bravo charlie', ' ', 2) == ['alpha', 'bravo', 'charlie']

    assert safe_split('alpha:bravo:charlie', ':', 1) == ['alpha', 'bravo:charlie']
    assert safe_split('alpha:bravo:charlie', ':', 1, reversed=True) == ['alpha:bravo', 'charlie']

    assert safe_split('alpha', ':', 1, []) == ['alpha', []]
    assert safe_split('alpha', ':', 1, [], reversed=True) == [[], 'alpha']


def test_format_id():
    item1 = 'a'
    item2 = 'b'
    my_list = [item1, item2]

    assert format_it(my_list) == "['a', 'b']"


def test_match_any():
    assert match_any('alpha', ['alpha', 'bravo']) == True
    assert match_any('bravo', ['alpha', 'bravo']) == True
    assert match_any('charlie', ['alpha', 'bravo']) == False
    assert match_any('one:alpha', ['one:.*', ]) == True
    assert match_any('two:alpha', ['one:.*', ]) == False
