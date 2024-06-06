import attrs
import collections


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
        self._tree.append(f"{path}.{name}: {dep._class.__name__}")

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

    class Dependency:

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


    class Requirements:

        def __init__(self, **dependencies):
            self.dependencies = collections.OrderedDict()
            for i_name, i_dep in dependencies.items():
                if not isinstance(i_dep, Appliance.Dependency):
                    i_dep = Appliance.Dependency(i_dep)
                self.dependencies[i_name] = i_dep


    __requirements__ = Requirements()
    appliances: Appliances = None

    def __attrs_post_init__(self):
        if self.appliances is None:
            self.appliances = Appliances()
        self.appliances.initialize(self, self.__class__.__requirements__)
