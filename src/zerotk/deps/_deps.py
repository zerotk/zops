from typing import Any
import functools
import click
from dataclasses import field, dataclass


# Dependency:


class Dependency:
    """
    Base class for all dependencies.
    The name "dependency" comes from the idea of "dependency injection".
    """

    def create(self, obj: Any, name: str) -> Any:
        """
        INTERFACE
        Returns the actual object using the strategy implemented in thes (Singleton, Factory, etc.)
        """
        raise NotImplementedError


# Dependency: Attribute


@dataclass
class Attribute(Dependency):

    class_: Any

    def __repr__(self):
        return f"<{self.__class__.__name__}({self.class_.__name__})>"

    def create(self, obj: Any, name):
        return self.class_()


# Dependency: Singleton


@dataclass
class Singleton(Dependency):
    """
    Declares a singleton dependency. Singleton instances are shared between all objects in a tree
    based on the attribute name and class name.

    TODO: Implement a way to replace a singleton with another "compatible" class. Check the
          compatibility using either subclasses or checking the actual class signature.

    IDEA: Add args/kwargs to constructor (if we ever need it).
    """

    class_: Any
    request: bool = False
    kwargs: dict = field(default_factory=dict)

    def __repr__(self):
        return f"<{self.__class__.__name__}({self.class_.__name__})>"

    def create(self, obj, name):
        key = (self.class_.__name__, name)
        shared_singleton = obj.deps.shared.setdefault(self.__class__.__name__, dict())
        result = shared_singleton.get(key, None)
        if result is None:
            if self.request:
                return "SingletonRequired"  #TODO: Return an object that fails if used.
            result = self.class_(
                deps=Deps(
                    shared=obj.deps.shared,
                    name=f"{obj.deps.name}.{name}"
                ),
                **self.kwargs
            )
            shared_singleton[key] = result
        return result


# Dependency: Factory


@dataclass
class Factory(Dependency):
    """
    Declares a factory dependency. A Factory is able to create new instances of the declared class.

    IDEA: Enable addition of args/kwargs on constructor and add them to the partial declaration on
          `.create` method.
    """

    class_: Any

    def __repr__(self):
        return f"<{self.__class__.__name__}({self.class_.__name__})>"

    def create(self, obj, name):
        """
        Returns the partial constructor for the declared class with the `deps` parameter assigned.
        """
        factory_function = self.class_
        result = functools.partial(
            factory_function,
            deps=Deps(shared=obj.deps.shared, name=f"{obj.deps.name}.{name}"),
        )
        return result


# Dependency: Command (using click)


@dataclass
class Command(Dependency):

    callback: Any = None

    def create(self, obj, name):
        """
        Create a click.command and stores the in the shared dict for future reference.
        (Is this really needed).
        """
        import types

        if isinstance(self.callback, types.FunctionType):
            result = click.command(self.callback)
            result.callback = types.MethodType(result.callback, obj)
        else:
            result = self.callback(
                deps=Deps(shared=obj.deps.shared, name=f"{obj.deps.name}.{name}")
            )
        return result


# Deps


class Declarations:
    """
    Implements Deps.declaration attribute holding all dependency declarations for an instance.
    """

    def __init__(self):
        self._items = dict()

    def add(self, name, decl):
        self._items[name] = decl

    def items(self):  # , filter_class=None):
        result = self._items.items()
        # if filter_class is not None:
        #   result = [i for i in result if isinstance(i[1], filter_class)]
        return result


@dataclass
class Deps:
    """
    Deps holds all information related with zerok.deps inner workings. Each instance have it's own
    instance of Deps as an instance attribute called ".deps".
    """

    # # Stores all dependency declarations for the instance. The declarations are the actual dependency
    # # objects declared in the class.
    # declarations: Declarations = field(default_factory=Declarations)

    name: str = field(default="")

    # The shared dictionary is shared between all deps instances in the same object tree. This is used
    # by Singleton dependency to shared information between different objects.
    shared: dict = field(default_factory=dict)


def instance__post_init(self):
    dependencies = {}
    assert hasattr(self, "deps")
    for i_name, i_decl in self.__deps_decl__.items():
        dependency = dependencies[i_name] = i_decl.create(self, i_name)
        self.deps.name = f"{self.deps.name}.{i_name}"
        setattr(self, i_name, dependency)


def instance__main(self):
    """
    Entrypoint for command line
    """

    def get_commands(obj):
        import types

        for i_name, i_decl in obj.__deps_decl__.items():
            if not isinstance(i_decl, Command):
                continue
            result = getattr(obj, i_name)
            if isinstance(getattr(result, "deps", None), Deps):
                result = create_group(result, i_name)
            yield i_name, result

        for i_name, i_decl in obj.__class__.__dict__.items():
            if not isinstance(i_decl, click.Command):
                continue
            result = getattr(obj, i_name)
            result.callback = types.MethodType(result.callback, obj)
            yield i_name, result

    def create_group(obj, name):
        @click.group(name)
        def result():
            pass

        for i_name, i_command in get_commands(obj):
            result.add_command(i_command)
        return result

    # import pdb;pdb.set_trace()
    result = create_group(self, "main")
    return result()


class MetaClass(type):

    def __new__(cls, clsname, clsbases, clsattrs):
        declarations = Declarations()
        for i_name, i_value in clsattrs.items():
            if isinstance(i_value, Dependency):
                declarations.add(i_name, i_value)

        annotations = clsattrs.setdefault("__annotations__", dict())
        annotations["deps"] = Deps

        clsattrs.update(
            dict(
                deps=field(default_factory=Deps),
                __deps_decl__=declarations,
                __post_init__=instance__post_init,
                main=instance__main,
            )
        )
        result = super().__new__(cls, clsname, clsbases, clsattrs)
        result = dataclass(result)
        return result


def define(maybe_cls=None, **kwargs):
    """
    Sharing the name with attrs.define, this class decorator enables zerotk.deps and attrs in a class
    without having to use subclasses.

    This is what this function does:
      * Adds deps:Deps declaration to the class
      * Add __attrs_post_init__ method implementation for the class. This method implements
        zerotk.deps initialization.
      * For each dependency declared in the class adds an attribute to the instance matching the
        declaration type.
    """

    def wrap(cls):
        return MetaClass(cls.__name__, cls.__bases__, dict(cls.__dict__))

    if maybe_cls is None:
        return wrap

    return wrap(maybe_cls)
