from collections import OrderedDict

import attrs

from zerotk.wiring import Appliance


@attrs.define
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

    def title(
        self, message: str, indent: int = 0, title_level: int = 1, verbosity: int = 0
    ):
        from rich.text import Text

        message = self._prefix(self.TITLE_PREFIX * title_level, indent=indent) + str(
            message
        )
        message = Text(message, style=self.TITLE_STYLE)
        self.secho(message, verbosity=verbosity)

    #     def execution(self, message, verbose=0):
    #         self._secho(['$'] + [message], self.EXECUTION_COLOR)
    #
    #     def setting(self, message, verbose=0):
    #         self._secho(['!'] + list(args), self.SETTING_COLOR)

    def item(
        self, message: str, indent: int = 0, style=OUTPUT_STYLE, verbosity: int = 0
    ):
        message = self._format_message(
            message, prefix=self.ITEM_PREFIX, indent=indent, style=style
        )
        self.secho(message, verbosity=verbosity)

    #     def output(self, *args):
    #         self._secho(args, self.OUTPUT_COLOR)
    #
    #     def response(self, *args):
    #         self._secho(['>'] + list(args), self.OUTPUT_COLOR)

    def info(self, message: str, indent: int = 0, verbosity: int = 0):
        message = self._format_message(
            message, prefix=self.INFO_PREFIX, indent=indent, style=self.INFO_STYLE
        )
        self.secho(message, verbosity=verbosity)

    def debug(self, message: str, indent: int = 0, verbosity: int = 0):
        message = self._format_message(
            message, prefix=self.DEBUG_PREFIX, indent=indent, style=self.DEBUG_COLOR
        )
        self.secho(message, verbosity=verbosity)

    def error(
        self,
        title: str,
        message: str = "",
        title_level: int = 1,
        indent: int = 0,
        verbosity: int = 0,
    ):
        title = self._format_message(
            title,
            prefix=self.ERROR_TITLE_PREFIX,
            indent=indent,
            style=self.ERROR_TITLE_COLOR,
        )
        self.secho(title, verbosity=verbosity)
        if message:
            message = self._format_message(
                message, prefix=None, indent=indent, style=self.ERROR_MESSAGE_COLOR
            )
            self.secho(message, verbosity=verbosity)

    def _format_message(self, message: str, prefix: str, indent: int, style: str):
        import rich.text

        result = self._prefix(prefix, indent=indent) + str(message)
        result = rich.text.Text(result, style)
        return result

    def _prefix(
        self, prefix: str, indent: int = 0, separator: str = SEPARATOR_CHAR
    ) -> str:
        result = self.INDENTATION_TEXT * indent
        if prefix is not None:
            result += prefix + separator
        return result

    def secho(self, message: str, fg=OUTPUT_STYLE, verbosity: int = 0) -> None:
        import rich

        if self.verbose_level < verbosity:
            return

        rich.print(message)

    def create_block(self, block_id, text):
        assert block_id not in self._blocks
        text = f"[white]{block_id}[/white]: {text}"
        self._blocks[block_id] = text
        self.secho(text)

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
        print(f"\x1b[{block_count}A", end="")
        print("\x1b[0J", end="")
        self.secho(block_text)
