import contextlib
import os


def urlconcat(*parts):
    """
    Concatenate URL parts properly handling slashes.

    This is a replacement for urljoin that have an specific and not wanted behaviour regaring slash handling.

    What we want is the following:

    * url_concat(http://alpha/bravo, zulu)    => http://alpha/bravo/zulu
    * url_concat(http://alpha/bravo/, zulu)   => http://alpha/bravo/zulu
    * url_concat(http://alpha/bravo//, zulu)  => http://alpha/bravo/zulu
    """
    result = []
    for i_part in parts:
        result.append(i_part.strip("/"))
    return "/".join(result)
