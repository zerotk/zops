import attrs
import collections
import click
import types
from collections import OrderedDict


class Appliances:

    class Tree:

        def __init__(self):
            self._name_stack = []
            self._tree_stack = []
            self.items = []

        def before_create(self, name, dep):
            self._name_stack.append(name)
            node = dict(
                tree_name=self.full_name,
                # dep=dep,
            )
            self._tree_stack.append(node)
            self.items.append(node)

        def after_create(self, app):
            self._name_stack.pop()
            node = self._tree_stack.pop()
            node["app"] = app

        @property
        def full_name(self):
            return ".".join(self._name_stack)

    tree = Tree()

    def __init__(self, **appliances):
        self.__appliances = appliances

    def __repr__(self):
        return f"<Appliance()>"

    def get(self, name):
        return self.__appliances.get(name)

    def set(self, name, app):
        if isinstance(app, Command):
            return
        self.__appliances[name] = app

    def initialize(self, obj, requirements):
        for i_name, i_dep in requirements.dependencies.items():
            app = self._initialize_app(i_name, i_dep)
            object.__setattr__(obj, i_name, app)

    def _initialize_app(self, name, dep):
        result = self.get(name)
        if result is None:
            result = dep.create(appliances=self, name=name)
            self.set(name, result)
        return result

    def create(self, name, class_, args, kwargs):
        self.tree.before_create(name, self)
        kwargs = kwargs.copy()
        if issubclass(class_, Appliance):
            kwargs["appliances"] = self
        result = class_(*args, **kwargs)
        self.tree.after_create(result)
        return result


@attrs.define(kw_only=True, slots=False)
class Appliance:

    define = attrs.define

    class _Base:
        pass

    class Requirements(_Base):

        def __init__(self, **dependencies):
            self.dependencies = collections.OrderedDict()
            for i_name, i_dep in dependencies.items():
                if not isinstance(i_dep, Appliance._Base):
                    i_dep = Appliance.Dependency(i_dep)
                self.dependencies[i_name] = i_dep

    class Dependency(_Base):

        def __init__(self, class_, *args, **kwargs):
            self._class = class_
            self._args = args
            self._kwargs = kwargs

        def __repr__(self):
            return f"<Dependency({self._class.__name__})>"

        def get_name(self):
            return self._class.__name__

        def issubclass(self, type_):
            return issubclass(self._class, type_)

        def create(self, appliances, name):
            result = appliances.create(
                name, self._class, self._args, self._kwargs
            )
            return result

    class Factory(_Base):

        def __init__(self, class_):
            self.__class = class_
            self.__appliances = None
            self.__full_name = None
            self.__count = 0

        def __repr__(self):
            return f"<Factory({self.__class.__name__})>"

        def get_name(self):
            return self.__class.__name__

        def create(self, appliances, name):
            appliances.tree.before_create(name, self)
            self.__appliances = appliances
            self.__full_name = appliances.tree.full_name
            appliances.tree.after_create(self)
            return self

        def __call__(self, *args, **kwargs):
            name=f"{self.__full_name}[{self.__count}]"
            result = self.__appliances.create(
                name, self.__class, args, kwargs
            )
            self.__count += 1
            return result

    __requirements__ = Requirements()
    appliances: Appliances = None

    def __attrs_post_init__(self):
        if self.appliances is None:
            self.appliances = Appliances()
        self.appliances.initialize(self, self.__class__.__requirements__)


class Command(Appliance):

    def _initialize_commands(self):
        appliance_commands = {
            i: getattr(self, i)
            for i
            in self.__requirements__.dependencies
            if isinstance(getattr(self, i), Command)
        }
        result = self._initialize_command("main", self)
        for i_name, i_app in appliance_commands.items():
            click_group = self._initialize_command(i_name, i_app)
            result.add_command(click_group)
        return result

    def _initialize_command(self, name, appliance_command):
        result = click.Group(name)
        for j_method in dir(appliance_command):
            click_command = getattr(appliance_command, j_method)
            if not isinstance(click_command, click.BaseCommand):
                continue
            click_command.callback = types.MethodType(click_command.callback, appliance_command)
            result.add_command(click_command)
        return result
    
    def main(self):
        click_command = self._initialize_commands()
        return click_command.main()