import attrs


class ConsoleLogger:

    def __init__(self, appliances=None):
        self.output = ""

    def secho(self, text):
        self.output += f"{text}\n"


class Dependency:

    class Requirement:

        def __init__(self, **dependencies):
            self.dependencies = dependencies


    class Appliances:

        def __init__(self, **appliances):
            self.__appliances = appliances
            self._tree = []
            self._name = ["<root>"]

        def get(self, name):
            return self.__appliances.get(name)

        def set(self, name, app):
            self.__appliances[name] = app

        def _record(self, name, dep):
            path = ".".join(self._name)
            self._tree.append(f"{path}.{name}: {dep._class.__name__}")

        def tree(self):
            return self._tree

        def initialize(self, obj, requirements):
            for i_name, i_dep in requirements.dependencies.items():
                self._record(i_name, i_dep)
                app = self.get(i_name)
                if app is None:
                    self._name.append(i_name)
                    app = i_dep.create(appliances=self)
                    self._name.pop()
                    self.set(i_name, app)
                object.__setattr__(obj, i_name, app)

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


@attrs.define(kw_only=True, slots=False)
class Appliance:

    injector = Dependency.Requirement()
    appliances: Dependency.Appliances = None

    def __init__(self, appliances=None):
        self.appliances = self.initialize(appliances)

    def __attrs_post_init__(self):
        if self.appliances is None:
            self.appliances = Dependency.Appliances()
        self.appliances.initialize(self, self.__class__.injector)



@attrs.define
class AlphaService(Appliance):

    injector = Dependency.Requirement(
        console=Dependency(ConsoleLogger)
    )
    name: str

    def run(self):
        self.console.secho(f"Alpha({self.name})")


@attrs.define
class BravoService(Appliance):

    injector = Dependency.Requirement(
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
    appliances = Dependency.Appliances(console=logger)
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
    appliances = Dependency.Appliances(console=logger)
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
