import attrs
from collections import OrderedDict
from typing import Any
import functools
import click


# Dependency:

class Dependency:
    """
    Base class for all dependencies.
    The name "dependency" comes from the idea of "dependency injection".
    """
    def create(self, obj:Any, name:str) -> Any:
      """
      INTERFACE
      Returns the actual object using the strategy implemented in thes (Singleton, Factory, etc.)
      """
      raise NotImplemented


# Dependency: Singleton

@attrs.define
class Singleton(Dependency):
    """
    Declares a singleton dependency. Singleton instances are shared between all objects in a tree
    based on the attribute name and class name.

    TODO: Implement a way to replace a singleton with another "compatible" class. Check the
          compatibility using either subclasses or checking the actual class signature.

    IDEA: Add args/kwargs to constructor (if we ever need it).
    """

    class_: Any

    def __repr__(self):
       return f"<{self.__class__.__name__}({self.class_.__name__})>"

    def create(self, obj, name):
      key = (self.class_.__name__, name)
      shared_singleton = obj.deps.shared.setdefault(self.__class__.__name__, dict())
      result = shared_singleton.get(key, None)
      if result is None:
        result = self.class_(deps=Deps(shared=obj.deps.shared, name=f"{obj.deps.name}.{name}"))
        shared_singleton[key] = result
      return result


# Dependency: Factory

@attrs.define
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
      result = functools.partial(
         self.class_,
         deps=Deps(shared=obj.deps.shared, name=f"{obj.deps.name}.{name}")
      )
      return result


# Dependency: Command (using click)

@attrs.define
class Command(Dependency):

  method: Any = None

  def create(self, obj, name):
    import types
    result = click.command(self.method)
    result.callback = types.MethodType(result.callback, obj)

    commands = obj.deps.shared.setdefault(self.__class__.__name__, dict())
    commands[name] = result

    return result

  def main(self):
    click_command = self._initialize_commands()
    return click_command.main()


# Deps

class Declarations:
    """
    Implements Deps.declaration attribute holding all dependency declarations for an instance.
    """

    def __init__(self):
       self._items = dict()

    def add(self, name, decl):
       self._items[name] = decl

    def items(self):
       return self._items.items()


@attrs.define
class Deps:
  """
  Deps holds all information related with zerok.deps inner workings. Each instance have it's own
  instance of Deps as an instance attribute called ".deps".
  """
  name: str = attrs.field(default="")

  # Stores all dependency declarations for the instance. The declarations are the actual dependency
  # objects declared in the class.
  declarations: Declarations = attrs.field(factory=Declarations)

  # The shared dictionary is shared between all deps instances in the same object tree. This is used
  # by Singleton dependency to shared information between different objects.
  shared: dict = attrs.field(factory=dict)


# attrs field/define

field = attrs.field

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
    cls.deps: Deps = attrs.field(factory=Deps)
    cls.__attrs_post_init__ = __attrs_post_init__
    return attrs.define(cls, slots=False, **kwargs)

  if maybe_cls is None:
      return wrap

  return wrap(maybe_cls)


def __attrs_post_init__(self):
  for i_name, i_decl in self.__class__.__dict__.items():
    if not isinstance(i_decl, Dependency):
      continue
    self.deps.declarations.add(i_name, i_decl)

  for i_name, i_decl in self.deps.declarations.items():
    attr = i_decl.create(self, i_name)
    if hasattr(attr, "deps"):
      attr.deps.name = f"{self.deps.name}.{i_name}"
    object.__setattr__(self, i_name, attr)
