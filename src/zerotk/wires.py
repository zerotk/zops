from zz.services.console import Console
import attrs
import sys


# =================================================================================================== zerotk.wires


class Wires:
    """
    Principals:
        1. Default usage need no boiler plate;
        2. No global magic. Everthing must be explicit;
    """

    class dependency:

        def __init__(self, class_, *args, **kwargs):
            self._class = class_
            self._args = args
            self._kwargs = kwargs

        def __repr__(self):
            return f"{self.__class__.__name__}[{self._class}]"

        def create(self, **kwargs):
            # Values passed during creation overwrite the default ones in the dependency declartion.
            self._kwargs.update(kwargs)
            print(f"DEBUG: dependency.create {self._args, self._kwargs.keys()}")
            return self._class(*self._args, **self._kwargs)


class Appliance:

    def __init__(self, wires: Wires):
        self.wires = wires

    @staticmethod
    def attrs_post_init(self):

        debug_params = []
        for i_attr in self.__attrs_attrs__:
            name = i_attr.alias
            if isinstance(i_attr.default, Wires.dependency):
                debug_params.append(f"+{name}")
            else:
                debug_params.append(f"-{name}")
        print(f"DEBUG: class {self.__class__.__name__}({', '.join(debug_params)})")

        # Collect initialized attributes to pass to this instance fields.
        inheritance_dependencies = {}
        for i_attr in self.__attrs_attrs__:
            name = i_attr.alias
            value = getattr(self, name)
            if not isinstance(value, Wires.dependency):
                inheritance_dependencies[name] = value

        # Replace Wires.dependency attributes with the actual values, either the declared default
        # or an inheritanced value.
        for i_attr in self.__attrs_attrs__:
            name = i_attr.alias
            value = getattr(self, name)
            if isinstance(value, Wires.dependency):
                print(f"DEBUG: .{name} = {value}({inheritance_dependencies}).")
                setattr(self, name, value.create(**inheritance_dependencies))

    def tree(self):
        result = {}
        return result