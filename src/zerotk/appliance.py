import attrs
import collections
import click
import types


class Appliances:

    def __init__(self, **appliances):
        self.__appliances = appliances
        self._tree = []
        self._name = ["<root>"]

    def __repr__(self):
        return f"<{self._name}>"

    def get(self, name):
        return self.__appliances.get(name)

    def set(self, name, app):
        self.__appliances[name] = app

    def _record(self, name, dep):
        path = ".".join(self._name)
        self._tree.append(f"{path}.{name}: {dep.get_name()}")

    def tree(self):
        return self._tree

    def initialize(self, obj, requirements):
        # print(f"DEBUG: initialize: {obj}")
        for i_name, i_dep in requirements.dependencies.items():
            # print(f"DEBUG: initialize.{i_name} = {i_dep}")
            self._record(i_name, i_dep)
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
            self._class = class_

        def __repr__(self):
            return f"<Factory[{self._class.__name__}]>"

        def get_name(self):
            return self._class.__name__

        def create(self, **kwargs):
            return self

        def __call__(self, *args, **kwargs):
            return self._class(*args, **kwargs)

    __requirements__ = Requirements()
    appliances: Appliances = None

    def __attrs_post_init__(self):
        if self.appliances is None:
            self.appliances = Appliances()
        self.appliances.initialize(self, self.__class__.__requirements__)


class Command(Appliance):

    # @classmethod
    # def as_click_command(cls, method, name=None, command_class=click.Command):
    #     import click
    #     import inspect
    #     import pathlib

    #     name = name or method

    #     appliances = Appliances()
    #     app = cls(appliances=appliances)
    #     callback = getattr(app, method)

    #     signature = inspect.signature(callback)
    #     params = []
    #     for i_name, i_parameter in signature.parameters.items():
    #         parameter_class = click.Argument
    #         parameter_kwargs = {
    #             "param_decls": [i_name],
    #             "type": i_parameter.annotation,
    #             "default": i_parameter.default,
    #         }
    #         match i_parameter.annotation.__name__:
    #             case "Path":
    #                 parameter_kwargs["type"] = click.Path()
    #             case "list":
    #                 parameter_kwargs["type"] = i_parameter.annotation
    #             case "bool":
    #                 parameter_class = click.Option
    #                 parameter_kwargs["is_flag"] = True
    #                 option_name = "--" + i_name.replace("_", "-")
    #                 parameter_kwargs["param_decls"] = [option_name]
    #             case _:
    #                 raise TypeError(i_parameter.annotation.__name__)

    #         p = parameter_class(**parameter_kwargs)
    #         params.append(p)

    #     result = command_class(
    #         name=name,
    #         callback=callback,
    #         params=params,
    #     )
    #     return result

    # def madin(self):
    #     click_cmd = self.as_click_command("__main__", command_class=click.Group)

    #     for i_name in self.__requirements__.dependencies:
    #         app = getattr(self, i_name)
    #         if not isinstance(app, Command):
    #             continue
    #         click_cmd.add_command(app.as_click_command("__run__"), name=i_name)
    #     return click_cmd.main()

    def initialize_cli(self):
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
        click_command = self.initialize_cli()
        return click_command.main()