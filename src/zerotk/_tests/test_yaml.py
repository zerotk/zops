def test_ordereddict():
    from collections import OrderedDict

    from zerotk.lib.text import dedent
    from zerotk.lib.yaml import yaml_load

    contents = yaml_load(
        dedent(
            """
              root:
                alpha: 1
                bravo: 2
                charlie: 3
                echo: 4
                foxtrot: 5
                golf: 6
                hotel: 7
            """
        )
    )
    assert isinstance(contents, OrderedDict)
    assert isinstance(contents["root"], OrderedDict)


def test_duplicate_keys():
    import pytest

    from zerotk.lib.text import dedent
    from zerotk.lib.yaml import DuplicateKeyError
    from zerotk.lib.yaml import yaml_load

    with pytest.raises(DuplicateKeyError):
        yaml_load(
            dedent(
                """
                  root:
                    alpha: 1
                    alpha: 2
                """
            )
        )
