from zz.services.text import Text


def test_dedent0():
    text = Text()
    string = text.dedent("oneline")
    assert string == "oneline"


def test_dedent1():
    text = Text()
    string = text.dedent(
        """
        oneline
        """
    )
    assert string == "oneline"


def test_dedent2():
    text = Text()
    string = text.dedent(
        """
        oneline
        twoline
        """
    )
    assert string == "oneline\ntwoline"


def test_dedent3():
    text = Text()
    string = text.dedent(
        """
        oneline
            tabbed
        """
    )
    assert string == "oneline\n    tabbed"


def test_dedent4():
    text = Text()
    string = text.dedent(
        """
        oneline
            tabbed
        detabbed
        """
    )
    assert string == "oneline\n    tabbed\ndetabbed"


def test_dedent5():
    text = Text()
    string = text.dedent(
        """
        oneline
        """,
        ignore_first_linebreak=False,
    )
    assert string == "\noneline"


def test_dedent6():
    text = Text()
    string = text.dedent(
        """
        oneline
        """,
        ignore_last_linebreak=False,
    )
    assert string == "oneline\n"


def test_dedent7():
    """
    Test a string that has an 'empty line' with 4 spaces above indent level
    """
    text = Text()
    # Using a trick to avoid auto-format to remove the empty spaces.
    string = text.dedent(
        """
        line
        %s
        other_line
        """
        % "    "
    )
    assert string == "line\n    \nother_line"


def test_dedent8():
    """
    Test not the first line in the right indent.
    """
    text = Text()
    string = text.dedent(
        """
            alpha
          bravo
        charlie
        """
    )
    assert string == "    alpha\n  bravo\ncharlie"


def test_dedent9():
    """
    Test behavior when using \t at the start of a string. .. seealso:: BEN-21 @ JIRA
    """
    text = Text()
    string = text.dedent(
        """
            alpha
        \tbravo
        """
    )
    assert string == "    alpha\n\tbravo"


def test_dedent10():
    """
    Checking how dedent handles empty lines at the end of string without parameters.
    """
    text = Text()
    string = text.dedent(
        """
        alpha
        """
    )
    assert string == "alpha"
    string = text.dedent(
        """
        alpha

        """
    )
    assert string == "alpha\n"
    string = text.dedent(
        """
        alpha


        """
    )
    assert string == "alpha\n\n"


def test_dedent11():
    """
    Check calling dedent more than once.
    """
    text = Text()
    string = text.dedent(
        """
        alpha
        bravo
        charlie
        """
    )
    assert string == "alpha\nbravo\ncharlie"
    string = text.dedent(string)
    assert string == "alpha\nbravo\ncharlie"
    string = text.dedent(string)
    assert string == "alpha\nbravo\ncharlie"


def test_indent():
    text = Text()
    assert text.indent("") == ""

    assert text.indent("alpha") == "    alpha"

    assert text.indent("alpha", indent_=2) == "        alpha"
    assert text.indent("alpha", indentation="...") == "...alpha"

    # If the original text ended with '\n' the resulting text must also end with '\n'
    assert text.indent("alpha\n") == "    alpha\n"

    # If the original text ended with '\n\n' the resulting text must also end with '\n\n'
    # Empty lines are not indented.
    assert text.indent("alpha\n\n") == "    alpha\n\n"

    # Empty lines are not indented nor cleared.
    assert text.indent("alpha\n  \ncharlie") == "    alpha\n  \n    charlie"

    # Empty lines are not indented nor cleared.
    assert text.indent(["alpha", "bravo"]) == "    alpha\n    bravo\n"

    # Multi-line test.
    assert text.indent("alpha\nbravo\ncharlie") == "    alpha\n    bravo\n    charlie"


def test_safe_split():
    text = Text()
    assert text.safe_split("alpha", " ") == ["alpha"]
    assert text.safe_split("alpha bravo", " ") == ["alpha", "bravo"]
    assert text.safe_split("alpha bravo charlie", " ") == ["alpha", "bravo", "charlie"]

    assert text.safe_split("alpha", " ", 1) == ["alpha", ""]
    assert text.safe_split("alpha bravo", " ", 1) == ["alpha", "bravo"]
    assert text.safe_split("alpha bravo charlie", " ", 1) == ["alpha", "bravo charlie"]

    assert text.safe_split("alpha", " ", 1, default=9) == ["alpha", 9]
    assert text.safe_split("alpha bravo", " ", 1, default=9) == ["alpha", "bravo"]
    assert text.safe_split("alpha bravo charlie", " ", 1, default=9) == [
        "alpha",
        "bravo charlie",
    ]

    assert text.safe_split("alpha", " ", 2) == ["alpha", "", ""]
    assert text.safe_split("alpha bravo", " ", 2) == ["alpha", "bravo", ""]
    assert text.safe_split("alpha bravo charlie", " ", 2) == ["alpha", "bravo", "charlie"]

    assert text.safe_split("alpha:bravo:charlie", ":", 1) == ["alpha", "bravo:charlie"]
    assert text.safe_split("alpha:bravo:charlie", ":", 1, reversed=True) == [
        "alpha:bravo",
        "charlie",
    ]

    assert text.safe_split("alpha", ":", 1, []) == ["alpha", []]
    assert text.safe_split("alpha", ":", 1, [], reversed=True) == [[], "alpha"]


def test_format_id():
    item1 = "a"
    item2 = "b"
    my_list = [item1, item2]
    text = Text()
    assert text.format_it(my_list) == "['a', 'b']"


def test_match_any():
    text = Text()
    assert text.match_any("alpha", ["alpha", "bravo"]) == True
    assert text.match_any("bravo", ["alpha", "bravo"]) == True
    assert text.match_any("charlie", ["alpha", "bravo"]) == False
    assert (
        text.match_any(
            "one:alpha",
            [
                "one:.*",
            ],
        )
        == True
    )
    assert (
        text.match_any(
            "two:alpha",
            [
                "one:.*",
            ],
        )
        == False
    )


def test_dedent():
    text = Text()
    assert (
        text.dedent(
            """
            root:
              alpha: 1
              bravo: 2
            """
        )
        == """root:\n  alpha: 1\n  bravo: 2\n"""
    )


def test_safesplit():
    text = Text()

    assert text.safe_split("alpha,bravo", ",", default="zulu", maxsplit=2) == ["alpha", "bravo"]
    assert text.safe_split("alpha", ",", default="zulu", maxsplit=2) == ["alpha", "zulu"]
    assert text.safe_split("alpha", ",", default="zulu", maxsplit=3) == ["alpha", "zulu", "zulu"]
    assert text.safe_split("alpha,bravo,charlie", ",", maxsplit=2) == [
        "alpha",
        "bravo",
        "charlie",
    ]
