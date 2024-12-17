from zerotk import deps
from zz.services.console import Console
from zz.services.formatter import Formatter


@deps.define
class CommandWrapper:
    """
    The idea here is to have both CLI and API with the same code.

    Is it possible?
    I don't know.
    """

    formatter = deps.Singleton(Formatter)
    console = deps.Singleton(Console)

    def items(self, items, header=False):
        from rich.table import Table

        table = Table()
        if header:
            table.title = header

        for i, i_item in enumerate(items):
            if isinstance(i_item, str):
                d = {"items": i_item}
            elif isinstance(i_item, dict):
                d = i_item
            elif hasattr(i_item, "as_dict"):
                d = i_item.as_dict()
            elif hasattr(i_item, "__annotations__"):
                d = {j: getattr(i_item, j) for j in i_item.__annotations__.keys()}
            else:
                raise RuntimeError(
                    f"Item does not implements either as_dict or __annotations__ interface. {i_item.__class__}"
                )

            if i == 0:
                for j in d.keys():
                    table.add_column(j)
            table.add_row(*d.values())

        self.console._print(table)


    def json(self, content):
        self.console._print(content)
