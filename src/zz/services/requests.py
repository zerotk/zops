import functools
from typing import Dict


class Requests:
    """
    Requests singleton.
    """

    @classmethod
    @functools.cache
    def singleton(cls) -> "Requests":
        return cls()

    def get(self, url: str, params: Dict = {}) -> any:
        """ """
        import ssl

        import requests
        import urllib3

        urllib3.disable_warnings()
        return requests.get(url, timeout=60, verify=ssl.CERT_NONE, params=params).json()
