import pytest


@pytest.mark.parametrize(
    "parts,expected,urljoin_expected",
    [
        (
            ("http://alpha/bravo/charlie", "zulu"),
            "http://alpha/bravo/charlie/zulu",
            "http://alpha/bravo/zulu",
        ),
        (
            ("http://alpha/bravo/charlie/", "zulu"),
            "http://alpha/bravo/charlie/zulu",
            "http://alpha/bravo/charlie/zulu",
        ),
        (
            ("http://alpha/bravo/charlie//", "zulu"),
            "http://alpha/bravo/charlie/zulu",
            "http://alpha/bravo/charlie/zulu",
        ),
        (
            ("http://alpha/bravo/charlie", "/zulu"),
            "http://alpha/bravo/charlie/zulu",
            "http://alpha/zulu",
        ),
        (
            ("http://alpha/bravo/charlie/", "/zulu"),
            "http://alpha/bravo/charlie/zulu",
            "http://alpha/zulu",
        ),
        (
            ("http://alpha/bravo/charlie//", "/zulu"),
            "http://alpha/bravo/charlie/zulu",
            "http://alpha/zulu",
        ),
    ],
)
def test_urlconcat(parts, expected, urljoin_expected):
    from urllib.parse import urljoin

    from zerotk.lib.url import urlconcat

    assert urlconcat(*parts) == expected
    assert urljoin(*parts) == urljoin_expected
