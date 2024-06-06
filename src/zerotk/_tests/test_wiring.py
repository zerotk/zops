import attrs
from zerotk.appliance import Appliance, Dependency, Requirements, Appliances


class ConsoleLogger:

    def __init__(self, appliances=None):
        self.output = ""

    def secho(self, text):
        self.output += f"{text}\n"



@attrs.define
class AlphaService(Appliance):

    __requirements__ = Requirements(
        console=Dependency(ConsoleLogger)
    )
    name: str

    def run(self):
        self.console.secho(f"Alpha({self.name})")


@attrs.define
class BravoService(Appliance):

    __requirements__ = Requirements(
        console=Dependency(ConsoleLogger),
        alpha=Dependency(AlphaService, "level_two"),
    )
    name: str

    def run(self):
        self.console.secho(f"Bravo({self.name})")
        self.alpha.run()


def test_1():
    # Test 1: Using the service without any boilder plate
    a = AlphaService(name="simplest")
    a.run()
    assert a.console.output == "Alpha(simplest)\n"
    assert a.appliances.tree() == [
        "<root>.console: ConsoleLogger"
    ]

def test_2():
    # Test 2: Overwriting a dependency
    logger = ConsoleLogger()
    appliances = Appliances(console=logger)
    a = AlphaService(appliances=appliances, name="overwriting")
    a.run()
    assert logger.output == "Alpha(overwriting)\n"
    assert a.console is logger
    assert a.appliances is appliances
    assert a.appliances.tree() == [
        "<root>.console: ConsoleLogger"
    ]

def test_3():
    # Test 3: Two level no boiler plate
    b = BravoService(name="test3")
    b.run()
    assert b.console.output == "Bravo(test3)\nAlpha(level_two)\n"
    assert b.appliances.tree() == [
        "<root>.console: ConsoleLogger",
        "<root>.alpha: AlphaService",
        "<root>.alpha.console: ConsoleLogger",
    ]

def test_4():
    # Test 4: Two level overwrite
    logger = ConsoleLogger()
    appliances = Appliances(console=logger)
    b = BravoService(appliances=appliances, name="bravo")
    b.run()
    assert logger.output == "Bravo(bravo)\nAlpha(level_two)\n"
    assert b.console is logger
    assert b.appliances is appliances
    assert b.alpha.console is logger
    assert b.alpha.appliances is appliances
    assert b.appliances.tree() == [
        "<root>.console: ConsoleLogger",
        "<root>.alpha: AlphaService",
        "<root>.alpha.console: ConsoleLogger",
    ]
