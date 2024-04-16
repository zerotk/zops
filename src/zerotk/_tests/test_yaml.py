def test_ordereddict():
    from zerotk.lib.yaml import yaml_load
    from zerotk.lib.text import dedent
    from collections import OrderedDict

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
    from zerotk.lib.yaml import yaml_load, DuplicateKeyError
    from zerotk.lib.text import dedent
    import pytest

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
