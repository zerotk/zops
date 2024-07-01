from zerotk import deps
import click
import pytest
import attrs
from dataclasses import field


def test_deps_metaclass():

    class Support(metaclass=deps.MetaClass):
        pass

    class Alpha(metaclass=deps.MetaClass):
        first: int
        second: int = 2
        third = deps.Singleton(Support)

    a = Alpha(first=1)
    assert a.first == 1
    assert a.second == 2


def test_behave_like_attrs():

    @attrs.define()
    class Alpha:
        first: int
        second: int = -1

    @deps.define()
    class Bravo:
        first: int
        second: int = -1

    a = Alpha(first=1, second=2)
    assert a.first == 1
    assert a.second == 2

    b = Bravo(first=1, second=2)
    assert b.first == 1
    assert b.second == 2


def test_deps_attr():

    @deps.define()
    class Alpha:
        first: int = 1
        second: int = field(default=2)

    a1 = Alpha()
    a2 = Alpha()
    assert isinstance(a1.deps, deps.Deps)
    assert a1.deps is not a2.deps


def test_declarations():

    @deps.define()
    class Utility:
        pass

    @deps.define()
    class Alpha:
        number: int = 0
        util = deps.Singleton(Utility)

    a = Alpha()
    assert list(a.__deps_decl__.items()) == [("util", Alpha.util)]


def test_deps_shared():

    @deps.define()
    class Alpha:
        pass

    a = Alpha()
    assert isinstance(a.__deps_decl__, deps.Declarations)
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
    assert a.__deps_decl__ is not b.__deps_decl__
    assert a.deps.shared is not b.deps.shared


def test_sub_object():

    @deps.define()
    class Alpha:
        pass

    @deps.define()
    class Bravo:
        alpha = deps.Singleton(Alpha)

    b = Bravo()
    assert list(b.__deps_decl__.items()) == [("alpha", Bravo.alpha)]
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


def test_command_simple():
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


def test_command_call():

    @deps.define()
    class Alpha:

        @click.command("test")
        @click.argument("subject", default="World")
        def anything(self, subject):
            """
            This is a test command.
            """
            print(f"Hello, {subject}!")

    a = Alpha()
    with pytest.raises(SystemExit) as e:
        a.main()
        assert e.retcode == 0


def test_sub_command():

    @deps.define()
    class Alpha:

        @click.command
        def test_alpha(self):
            """
            This is alpha.
            """
            print("Hello from Alpha.")

    @deps.define()
    class Bravo:

        alpha = deps.Command(Alpha)

        @click.command
        def test_bravo(self):
            """
            This is bravo.
            """
            print("Hello from Bravo.")

    b = Bravo()
    with pytest.raises(SystemExit) as e:
        b.main()
        assert e.retcode == 0
