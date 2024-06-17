import attrs
from collections import OrderedDict
from typing import Any
import functools


# Dependency:

class Dependency:
    pass


# Dependency: Singleton

@attrs.define
class Singleton(Dependency):
    class_: Any

    def __repr__(self):
       return f"<{self.__class__.__name__}({self.class_.__name__})>"

    def create(self, deps, name):
       key = (self.class_.__name__, name)
       shared_singleton = deps.shared.setdefault("Singleton", dict())
       result = shared_singleton.get(key, None)
       if result is None:
          result = self.class_(deps=Deps(shared=deps.shared))
          shared_singleton[key] = result
       return result


# Dependency: Factory

@attrs.define
class Factory(Dependency):
    class_: Any
    callback = None

    def __repr__(self):
       return f"<{self.__class__.__name__}({self.class_.__name__})>"

    def create(self, deps, name):
       result = functools.partial(self.class_, deps=Deps(shared=deps.shared))
       return result


# Deps

class Declarations(OrderedDict):

    def add(self, name, dep):
       self[name] = dep


@attrs.define
class Deps:
  declarations: Declarations = attrs.field(factory=Declarations)
  shared: dict = attrs.field(factory=dict)


# define

def define(maybe_cls=None, **kwargs):

  def __attrs_post_init__(self):
    print(f"{self.__class__.__name__}({id(self)}).__attrs_post_init__")
    for i_name, i_decl in self.__class__.__dict__.items():
      if not isinstance(i_decl, Dependency):
        continue
      self.deps.declarations.add(i_name, i_decl)
      print(f"  .{i_name} = {i_decl}")

    for i_name, i_decl in self.deps.declarations.items():
      attr = i_decl.create(self.deps, i_name)
      object.__setattr__(self, i_name, attr)

  def wrap(cls):
    cls.deps: Deps = attrs.field(factory=Deps)
    cls.__attrs_post_init__ = __attrs_post_init__
    return attrs.define(cls, slots=False, **kwargs)

  if maybe_cls is None:
      return wrap

  return wrap(maybe_cls)


field = attrs.field
