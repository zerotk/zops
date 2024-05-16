def assert_file_contents(filename, expected):
    import os

    from datadiff.tools import assert_equal

    from zerotk.lib.text import dedent

    assert os.path.isfile(filename), "{}: File does not exists.".format(filename)
    obtained = open(filename, "r").read()

    expected = dedent(expected)

    assert_equal(obtained, expected)
