from zz.services.console import Console
import attrs
import sys
from zerotk.wires import Wires, Appliance
import zerotk.text


class ConsoleLogger:

    def __init__(self):
        self.output = ""

    def secho(self, text):
        self.output += f"{text}\n"


@attrs.define(kw_only=True)
class ConsoleUser(Appliance):

    console: attrs.field = Wires.dependency(Console)

    name: str = "ConsoleUser"

    def __attrs_pre_init__(self):
        super().__init__(wires=Wires())

    __attrs_post_init__ = Appliance.attrs_post_init

    def run(self):
        self.console.secho(f"ConsoleUser({self.name})")



@attrs.define(kw_only=True)
class ConsoleTwoUser(Appliance):

    console2: attrs.field = Wires.dependency(Console)

    name: str = "ConsoleUser"

    __attrs_post_init__ = Appliance.attrs_post_init

    def run(self):
        self.console2.secho(f"ConsoleTwoUser({self.name})")


def test_single_level():

    @attrs.define(kw_only=True)
    class SingleLevelApp(Appliance):

        console: attrs.field = Wires.dependency(Console)

        __attrs_post_init__ = Appliance.attrs_post_init

        def run(self):
            self.console.secho("SimpleAppliance")

    logger = ConsoleLogger()
    a = SingleLevelApp(console=logger)
    a.run()
    assert logger.output == "SimpleAppliance\n"


def test_two_levels():

    @attrs.define(kw_only=True)
    class DoubleLevelApp(Appliance):

        console: attrs.field = Wires.dependency(Console)

        level2: attrs.field = Wires.dependency(ConsoleUser, name="level2")

        __attrs_post_init__ = Appliance.attrs_post_init

        def run(self):
            self.console.secho("DoubleAppliance")
            self.level2.run()

    logger = ConsoleLogger()
    a = DoubleLevelApp(console=logger)
    a.run()
    assert logger.output == "DoubleAppliance\nConsoleUser(level2)\n"


def test_three_levels():

    @attrs.define(kw_only=True)
    class MiddleLevelApp(Appliance):

        console: attrs.field = Wires.dependency(Console)

        level3: attrs.field = Wires.dependency(ConsoleUser, name="level3")

        name: str

        __attrs_post_init__ = Appliance.attrs_post_init

        def run(self):
            self.console.secho(f"MiddleLevelApp({self.name})")
            self.level3.run()

    @attrs.define(kw_only=True)
    class TopLevelApp(Appliance):

        console: attrs.field = Wires.dependency(Console)

        level2: attrs.field = Wires.dependency(MiddleLevelApp, name="level2")

        name: str

        __attrs_post_init__ = Appliance.attrs_post_init

        def run(self):
            self.console.secho(f"TopLevelApp({self.name})")
            self.level2.run()

    logger = ConsoleLogger()
    a = TopLevelApp(console=logger, name="top")
    a.run()
    assert logger.output == "TopLevelApp(top)\nMiddleLevelApp(level2)\nConsoleUser(level3)\n"


# def test():
#     # Normal use. No boiler plate
#     # greeter = Greeter()
#     # greeter.run()
#
#     # # Custom use. Tests
#     logger = ConsoleLogger()
#     greeter = Greeter(console=logger)
#     greeter.run()
#     assert logger.output == zerotk.text.dedent(
#         """
#         Getting word 'Hello'
#         Getting word 'World'
#         Hello, World!
#
#         """
#     )
