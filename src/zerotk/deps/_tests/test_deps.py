from zerotk import deps
import click
import pytest


def test_deps():

  @deps.define()
  class Alpha:
    pass

  a = Alpha()
  assert isinstance(a.deps, deps.Deps)


def test_declarations():

  @deps.define()
  class Utility:
    pass

  @deps.define()
  class Alpha:
    number: int = 0
    util = deps.Singleton(Utility)

  a = Alpha()
  assert list(a.deps.declarations.items()) == [("util", Alpha.util)]


def test_deps_shared():

  @deps.define()
  class Alpha:
    pass

  a = Alpha()
  assert isinstance(a.deps.declarations, deps.Declarations)
  assert isinstance(a.deps.shared, dict)


def test_different_stuff():

  @deps.define()
  class Alpha:
    pass

  @deps.define()
  class Bravo:
    pass

  a = Alpha()
  b = Bravo()
  assert a.deps is not b.deps
  assert a.deps.declarations is not b.deps.declarations
  assert a.deps.shared is not b.deps.shared


def test_sub_object():

  @deps.define()
  class Alpha:
    pass

  @deps.define()
  class Bravo:
    alpha = deps.Singleton(Alpha)

  b = Bravo()
  assert list(b.deps.declarations.items()) == [("alpha", Bravo.alpha)]
  assert isinstance(b.alpha, Alpha)


def test_different_deps_tree():

  @deps.define()
  class Alpha:
    pass

  @deps.define()
  class Bravo:
    alpha = deps.Singleton(Alpha)

  @deps.define()
  class Charlie:
    alpha = deps.Singleton(Alpha)

  b = Bravo()
  c = Charlie()
  assert b.alpha is not c.alpha


def test_same_deps_tree():

  @deps.define()
  class Alpha:
    pass

  @deps.define()
  class Bravo:
    alpha = deps.Singleton(Alpha)

  @deps.define()
  class Charlie:
    alpha = deps.Singleton(Alpha)

  my_deps = deps.Deps()
  b = Bravo(deps=my_deps)
  c = Charlie(deps=my_deps)
  assert b.alpha is c.alpha


def test_same_singleton_all_the_way_down():

  @deps.define()
  class Utility:
    pass

  @deps.define()
  class Alpha:
    util = deps.Singleton(Utility)

  @deps.define()
  class Bravo:
    util = deps.Singleton(Utility)
    parent = deps.Singleton(Alpha)

  @deps.define()
  class Charlie:
    alpha = deps.Singleton(Bravo)
    parent = deps.Singleton(Bravo)

  @deps.define()
  class Delta:
    util = deps.Singleton(Utility)
    parent = deps.Singleton(Charlie)

  d = Delta()
  assert id(d.deps.shared) == id(d.parent.deps.shared)
  assert id(d.deps.shared) == id(d.parent.parent.deps.shared)
  assert id(d.deps.shared) == id(d.parent.parent.parent.deps.shared)

  assert getattr(d.parent, "util", None) is None
  assert d.util is d.parent.parent.util
  assert d.util is d.parent.parent.parent.util


def test_factory():

  @deps.define()
  class Item:
    index: int = deps.field()

  @deps.define()
  class Alpha:
    item_factory = deps.Factory(Item)

    def create_items(self, count):
      result = []
      for i in range(count):
        r = self.item_factory(index=i)
        result.append(r)
      return result

  a = Alpha()
  r = a.create_items(5)
  assert len(r) == 5
  assert isinstance(r[0], Item)


def test_command():

  @deps.define()
  class Alpha:

    @deps.Command
    @click.argument("subject")
    def test(self, subject):
      """
      This is a test command.
      """
      print(f"Hello, {subject}!")

  a = Alpha()
  with pytest.raises(SystemExit) as e:
    a.test(["there"])
    assert e.retcode == 0


def test_sub_command():

  @deps.define()
  class Alpha:

    @deps.Command
    def test_alpha(self):
      """
      This is alpha.
      """
      print(f"Hello from Alpha.")

  @deps.define()
  class Bravo:

    alpha = deps.Command(Alpha)

    @deps.Command
    def test_bravo(self):
      """
      This is bravo.
      """
      print("Hello from Bravo.")

  b = Bravo()
  with pytest.raises(SystemExit) as e:
    b.main()
    assert e.retcode == 0
