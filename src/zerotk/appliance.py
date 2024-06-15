import attrs
import collections
import click
import types


class Appliances:

    def __init__(self, **appliances):
        self.__appliances = appliances
        self._tree = []
        self._name = []

    def __repr__(self):
        return f"<{id(self)}>"

    def get(self, name):
        return self.__appliances.get(name)

    def set(self, name, app):
        if isinstance(app, Command):
            return
        self.__appliances[name] = app

    def _tree_record(self, name, dep):
        path = ".".join(self._name + [name])
        self._tree.append(f"{path} = {dep.get_name()}")

    def tree(self):
        return self._tree

    def initialize(self, obj, requirements):
        for i_name, i_dep in requirements.dependencies.items():
            self._tree_record(i_name, i_dep)
            app = self.get(i_name)
            if app is None:
                self._name.append(i_name)
                app = i_dep.create(appliances=self)
                self._name.pop()
                self.set(i_name, app)
            object.__setattr__(obj, i_name, app)


@attrs.define(kw_only=True, slots=False)
class Appliance:

    define = attrs.define

    class Requirements:

        def __init__(self, **dependencies):
            self.dependencies = collections.OrderedDict()
            for i_name, i_dep in dependencies.items():
                if not isinstance(i_dep, Appliance._Base):
                    i_dep = Appliance.Dependency(i_dep)
                self.dependencies[i_name] = i_dep

    class _Base:
        pass

    class Dependency(_Base):

        def __init__(self, class_, *args, **kwargs):
            self._class = class_
            self._args = args
            self._kwargs = kwargs

        def __repr__(self):
            return f"<Dependency[{self._class}]>"

        def get_name(self):
            return self._class.__name__

        def issubclass(self, type_):
            return issubclass(self._class, type_)

        def create(self, **kwargs):
            # Values passed during creation overwrite the default ones in the dependency declartion.
            self._kwargs.update(kwargs)
            return self._class(*self._args, **self._kwargs)

    class Factory(_Base):

        def __init__(self, class_):
            self.__class = class_
            self.__appliances = None

        def __repr__(self):
            return f"<Factory[{self.__class.__name__}]>"

        def get_name(self):
            return self.__class.__name__

        def create(self, appliances, **kwargs):
            self.__appliances = appliances
            return self

        def __call__(self, *args, **kwargs):
            return self.__class(appliances=self.__appliances, *args, **kwargs)

    __requirements__ = Requirements()
    appliances: Appliances = None

    def __attrs_post_init__(self):
        if self.appliances is None:
            self.appliances = Appliances()
        self.appliances.initialize(self, self.__class__.__requirements__)


class Command(Appliance):

    def _initialize(self):
        appliance_commands = {
            i_name: getattr(self, i_name)
            for i_name, _dep
            in self.__requirements__.dependencies.items()
            if isinstance(getattr(self, i_name), Command)
        }

        result = self._fix_command("main", self)
        for i_name, i_app in appliance_commands.items():
            click_group = self._fix_command(i_name, i_app)
            result.add_command(click_group)
        return result

    def _fix_command(self, name, appliance_command):
        result = click.Group(name)
        for j_method in dir(appliance_command):
            click_command = getattr(appliance_command, j_method)
            if not isinstance(click_command, click.BaseCommand):
                continue
            click_command.callback = types.MethodType(click_command.callback, appliance_command)
            result.add_command(click_command)
        return result
    
    def main(self):
        click_command = self._initialize()
        return click_command.main()