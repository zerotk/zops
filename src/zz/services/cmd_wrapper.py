import functools
from typing import Any

import boto3

from zerotk import deps
from zz.services.formatter import Formatter
from zz.services.console import Console


@deps.define
class CommandWrapper:
    """
    The idea here is to have both CLI and API with the same code.

    Is it possible?
    I don't know.
    """
    formatter = deps.Singleton(Formatter)
    console = deps.Singleton(Console)

    class Result:
        def __init__(self, header, items):
            self.header = header
            self.items = items

    def items(self, items, header=False):
        header = ""
        if isinstance(items, self.Result):
            header = items.header
            items = items.items
        if header:
            self.console.title(header)
        for i in items:
            self.console.item(i)
