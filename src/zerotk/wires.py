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
        return appliance.singleton()


class ConsoleLogger:
    
    def __init__(self):
        self.output = ""
    
    def secho(self, text):
        self.output += text


@attrs.define
class Greeter:

    console: attrs.field = Wires.appliance(Console)
    greeting: str = "Hello"

    def run(self, name="World!"):
        self.console.secho(f"{self.greeting}, {name}")


# Normal use. No boiler plate
greeter = Greeter()
greeter.run()

# Custom use. Tests
console = ConsoleLogger()
greeter = Greeter(console=console)
greeter.run()
assert console.output == "Hello, World!"