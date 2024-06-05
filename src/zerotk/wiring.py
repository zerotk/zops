import attrs
import collections


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
            if not isinstance(i_dep, Dependency):
                i_dep = Dependency(i_dep)
            self.dependencies[i_name] = i_dep


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

    injector = Requirements()
    appliances: Appliances = None

    def __attrs_post_init__(self):
        if self.appliances is None:
            self.appliances = Appliances()
        self.appliances.initialize(self, self.__class__.injector)


# # =================================================================================================== zerotk.wires
#
#
# class Wires:
#     """
#     Principals:
#         1. Default usage need no boiler plate;
#         2. No global magic. Everthing must be explicit;
#     """
#
#     class dependency:
#
#         def __init__(self, class_, *args, **kwargs):
#             self._class = class_
#             self._args = args
#             self._kwargs = kwargs
#
#         def __repr__(self):
#             return f"{self.__class__.__name__}[{self._class}]"
#
#         def create(self, **kwargs):
#             # Values passed during creation overwrite the default ones in the dependency declartion.
#             self._kwargs.update(kwargs)
#             print(f"DEBUG: dependency.create {self._args, self._kwargs.keys()}")
#             return self._class(*self._args, **self._kwargs)
#
#
# class Appliance:
#
#     def __init__(self, wires: Wires):
#         self.wires = wires
#
#     @staticmethod
#     def attrs_post_init(self):
#
#         debug_params = []
#         for i_attr in self.__attrs_attrs__:
#             name = i_attr.alias
#             if isinstance(i_attr.default, Wires.dependency):
#                 debug_params.append(f"+{name}")
#             else:
#                 debug_params.append(f"-{name}")
#         print(f"DEBUG: class {self.__class__.__name__}({', '.join(debug_params)})")
#
#         # Collect initialized attributes to pass to this instance fields.
#         inheritance_dependencies = {}
#         for i_attr in self.__attrs_attrs__:
#             name = i_attr.alias
#             value = getattr(self, name)
#             if not isinstance(value, Wires.dependency):
#                 inheritance_dependencies[name] = value
#
#         # Replace Wires.dependency attributes with the actual values, either the declared default
#         # or an inheritanced value.
#         for i_attr in self.__attrs_attrs__:
#             name = i_attr.alias
#             value = getattr(self, name)
#             if isinstance(value, Wires.dependency):
#                 print(f"DEBUG: .{name} = {value}({inheritance_dependencies}).")
#                 setattr(self, name, value.create(**inheritance_dependencies))
#
#     def tree(self):
#         result = {}
#         return result