from typing import Iterable
from typing import Tuple

from zerotk import deps

from .console import Console


@deps.define
class Formatter:
    """
    String formatter service.
    """

    console = deps.Singleton(Console)

    def dumps(self, obj: any) -> str:
        import json
        from datetime import datetime

        class DateTimeEncoder(json.JSONEncoder):
            def default(self, z):
                if isinstance(z, datetime):
                    return z.isoformat()
                else:
                    return super().default(z)

        return json.dumps(obj, indent=2, cls=DateTimeEncoder)

    def split_ssm_param(self, name_value: str) -> Tuple[str, str, str]:
        """
        Split a SSM parameter value_value string into it's three components.
        """
        import re

        name_value_regex = re.compile(
            r"(?P<name>[\/\w]*)(?::(?P<type>\w*))?=(?P<value>.*)$"
        )
        m = name_value_regex.match(name_value)
        if m is None:
            raise RuntimeError(f"Can't regex the line: {name_value!r}")
        r_name, r_type, r_value = m.groups()
        r_type = r_type or "String"
        return r_name, r_type, r_value

    def print_items(
        self, items: Iterable[str], indent: int = 0, item_format: str = ""
    ) -> None:
        if isinstance(items, dict):
            items = [dict(name=i, value=j) for i, j in sorted(items.items())]
        for i in items:
            if item_format == "":
                self.console.item(f"{i}")
                continue
            if hasattr(i, "as_dict"):
                i = i.as_dict()
            self.console.item(item_format.format(**i), indent=indent)
