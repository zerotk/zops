from collections import OrderedDict
from zerotk.appliance import Appliance
from rich.console import Console
import attrs


@Appliance.define
class Console(Appliance):

    TITLE_STYLE = "blue"
    EXECUTION_COLOR = "green"
    SETTING_COLOR = "blue"
    OUTPUT_STYLE = None
    INFO_STYLE = "white"
    DEBUG_COLOR = "red"
    ERROR_TITLE_COLOR = "red"
    ERROR_MESSAGE_COLOR = None

    SEPARATOR_CHAR = " "
    INDENTATION_TEXT = "  "

    ITEM_PREFIX = "*"
    TITLE_PREFIX = "#"
    DEBUG_PREFIX = "***"
    INFO_PREFIX = "\U0001F6C8"
    ERROR_TITLE_PREFIX = "!!!"

    verbose_level: int = 0
    _blocks = OrderedDict()
    _console = Console(highlight=False)

    @attrs.define
    class ConsoleStyle:
        color: str = "white"
        prefix: str = ""
        prefix_sep: str = " "
        indent: int = 0
        indent_char: str = "  "

        def format_message(self, message):
            result = self.indent * self.indent_char
            result += self.prefix + self.prefix_sep
            result += f"[{self.color}]{message}[/{self.color}]"
            return result

    STYLES = {
        "title": ConsoleStyle(
            color="blue",
        ),
        "item": ConsoleStyle(
            color="white",
            prefix="\U0001F784",
        ),
        "info": ConsoleStyle(
            color="white",
            prefix="\U0001F6C8",
        ),
        "debug": ConsoleStyle(
            color="white",
            prefix="\U0001F41B",
        ),
        "warning": ConsoleStyle(
            color="yellow",
            prefix="\U000026A0",
        ),
        "error": ConsoleStyle(
            color="red",
            prefix="\U0001F6C7",
        ),
    }

    def title(
        self,
        message: str,
        verbosity: int = 0,
        **kwargs,
    ):
        style = self.STYLES["title"]
        style = attrs.evolve(style, **kwargs)
        self._print(message=message, style=style)

    def item(
        self,
        message: str,
        verbosity: int = 0,
        **kwargs,
    ):
        style = self.STYLES["item"]
        style = attrs.evolve(style, **kwargs)
        self._print(message=message, style=style)

    def info(
        self,
        message: str,
        verbosity: int = 0,
        **kwargs,
    ):
        style = self.STYLES["info"]
        style = attrs.evolve(style, **kwargs)
        self._print(message=message, style=style)

    def debug(
        self,
        message: str,
        verbosity: int = 0,
        **kwargs,
    ):
        style = self.STYLES["debug"]
        style = attrs.evolve(style, **kwargs)
        self._print(message=message, style=style)

    def warning(
        self,
        message: str,
        verbosity: int = 0,
        **kwargs,
    ):
        style = self.STYLES["warning"]
        style = attrs.evolve(style, **kwargs)
        self._print(message=message, style=style)

    def error(
        self,
        message: str,
        verbosity: int = 0,
        **kwargs,
    ):
        style = self.STYLES["error"]
        style = attrs.evolve(style, **kwargs)
        self._print(message=message, style=style)

    def _print(self, message, style=ConsoleStyle()):
        message = style.format_message(message)
        self._console.print(message)

#     def _format_message(self, message: str, prefix: str, indent: int, style: str):
#         result = self._prefix(prefix, indent=indent) + str(message)
#         return result
#
#     def _prefix(
#         self, prefix: str, indent: int = 0, separator: str = SEPARATOR_CHAR
#     ) -> str:
#         result = self.INDENTATION_TEXT * indent
#         if prefix is not None:
#             result += prefix + separator
#         return result
#
#     def secho(self, message: str, verbosity: int = 0) -> None:
#
#         if self.verbose_level < verbosity:
#             return
#
#         self._console.print(message, highlight=False)

    def create_block(self, block_id, text):
        assert block_id not in self._blocks
        text = f"[white]{block_id}[/white]: {text}"
        self._blocks[block_id] = text
        self._print(text)

    def update_block(self, block_id, text):
        assert block_id in self._blocks
        text = f"[white]{block_id}[/white]: {text}"
        self._blocks[block_id] = text
        self._redraw_blocks()

    def clear_blocks(self):
        self._blocks.clear()

    def _redraw_blocks(self):
        block_text = "\n".join(self._blocks.values())
        block_count = len(self._blocks)
        # TODO: Use console for this.
        print(f"\x1b[{block_count}A", end="")
        print("\x1b[0J", end="")
        self._print(block_text)
