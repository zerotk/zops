def test_dedent():
    from zerotk.lib.text import dedent

    assert (
        dedent(
            """
          root:
            alpha: 1
            bravo: 2
        """
        )
        == """root:\n  alpha: 1\n  bravo: 2\n"""
    )


def test_safesplit():
    from zerotk.lib.text import safesplit

    assert safesplit("alpha,bravo", ",", default="zulu", size=2) == ["alpha", "bravo"]
    assert safesplit("alpha", ",", default="zulu", size=2) == ["alpha", "zulu"]
    assert safesplit("alpha", ",", default="zulu", size=3) == ["alpha", "zulu", "zulu"]
    assert safesplit("alpha,bravo,charlie", ",", size=2) == [
        "alpha",
        "bravo",
        "charlie",
    ]
