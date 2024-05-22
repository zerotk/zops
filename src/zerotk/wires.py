from zz.services.console import Console
import attrs

class Wires:
    """
    Principals:
        1. Default usage need no boiler plate;
        2. No global magic. Everthing must be explicit;
    """

    @classmethod
    def appliance(cls, appliance):
        return appliance()


class ConsoleLogger:

    def __init__(self):
        self.output = ""

    def secho(self, text):
        self.output += text


@attrs.define
class Another:

    console: attrs.field = Wires.appliance(Console)

    def run(self, name):
        self.console.secho(f"This is another class, {name}.")

@attrs.define
class Greeter:

    console: attrs.field = Wires.appliance(Console)
    greeting: str = "Hello"
    another: attrs.field = Wires.appliance(Another)

    def run(self, name="World"):
        self.console.secho(f"{self.greeting}, {name}!")
        self.another.run(name)


# Normal use. No boiler plate
greeter = Greeter()
greeter.run()

# Custom use. Tests
console = ConsoleLogger()
import pdb;pdb.set_trace()
greeter = Greeter(console=console)
greeter.run()

# The console should apply to both Greeter and Another automagically.
assert console.output == """Hello, World!
This is another class, World.
"""