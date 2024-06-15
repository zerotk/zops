import functools
from typing import Any

import boto3

from zerotk.appliance import Appliance
from zz.services.formatter import Formatter
from zz.services.console import Console


@Appliance.define
class CommandWrapper(Appliance):
    """
    The idea here is to have both CLI and API with the same code.

    Is it possible?
    I don't know.
    """

    __requirements__ = Appliance.Requirements(
        formatter = Formatter,
        console = Console,
    )

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
