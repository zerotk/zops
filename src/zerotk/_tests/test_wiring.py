from zz.services.console import Console


class ConsoleLogger:

    def __init__(self, appliances=None):
        self.output = ""

    def secho(self, text):
        self.output += f"{text}\n"


class Dependency:

    class Requirement:

        def __init__(self, **dependencies):
            self.__dependencies = dependencies

        def initialize(self, obj, fullfilment):
            if fullfilment is None:
                print(f"DEBUG: {obj} : Appliances() - This should appear zero or one time.")
                fullfilment = Dependency.Fullfilment()

            for i_name, i_dep in self.__dependencies.items():
                app = fullfilment.get(i_name)
                if app is None:
                    print(f"DEBUG: {obj} : create dependency")
                    app = i_dep.create(appliances=fullfilment)
                    fullfilment.set(i_name, app)
                else:
                    print(f"DEBUG: {obj} : reuse dependency")
                print(f"DEBUG: {obj}.{i_name} = {app}")
                setattr(obj, i_name, app)

            return fullfilment


    class Fullfilment:

        def __init__(self, **appliances):
            self.__appliances = appliances

        def get(self, name):
            return self.__appliances.get(name)

        def set(self, name, app):
            self.__appliances[name] = app

    def __init__(self, class_, *args, **kwargs):
        self._class = class_
        self._args = args
        self._kwargs = kwargs

    def __repr__(self):
        return f"{self.__class__.__name__}[{self._class}]"

    def create(self, **kwargs):
        # Values passed during creation overwrite the default ones in the dependency declartion.
        self._kwargs.update(kwargs)
        return self._class(*self._args, **self._kwargs)


class AlphaService:

    injector = Dependency.Requirement(
        console=Dependency(ConsoleLogger)
    )

    def __init__(self, name, appliances=None):
        self.name = name
        self.appliances = self.injector.initialize(self, appliances)

    def run(self):
        self.console.secho(f"Alpha({self.name})")


class BravoService:

    injector = Dependency.Requirement(
        console=Dependency(ConsoleLogger),
        alpha=Dependency(AlphaService, "level_two"),
    )

    def __init__(self, name, appliances=None):
        self.name = name
        self.appliances = self.injector.initialize(self, appliances)

    def run(self):
        self.console.secho(f"Bravo({self.name})")
        self.alpha.run()


def test_1():
    # Test 1: Using the service without any boilder plate
    a = AlphaService("simplest")
    a.run()
    assert a.console.output == "Alpha(simplest)\n"

def test_2():
    # Test 2: Overwriting a dependency
    logger = ConsoleLogger()
    appliances = Dependency.Fullfilment(console=logger)
    a = AlphaService(appliances=appliances, name="overwriting")
    a.run()
    assert logger.output == "Alpha(overwriting)\n"
    assert a.console is logger
    assert a.appliances is appliances

def test_3():
    # Test 3: Two level no boiler plate
    b = BravoService(name="test3")
    b.run()
    assert b.console.output == "Bravo(test3)\nAlpha(level_two)\n"

def test_4():
    # Test 4: Two level overwrite
    logger = ConsoleLogger()
    appliances = Dependency.Fullfilment(console=logger)
    b = BravoService(appliances=appliances, name="bravo")
    b.run()
    assert logger.output == "Bravo(bravo)\nAlpha(level_two)\n"
    assert b.console is logger
    assert b.appliances is appliances
    assert b.alpha.console is logger
    assert b.alpha.appliances is appliances


def test_print():
    # Test 4: Two level overwrite
    logger = ConsoleLogger()
    appliances = Dependency.Fullfilment(console=logger)
    b = BravoService(appliances=appliances, name="bravo")

    assert appliances.tree() == {}

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
