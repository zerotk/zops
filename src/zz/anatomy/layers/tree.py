import os
import pathlib
from collections import OrderedDict

from zerotk import deps
from zz.services.template_engine import TemplateEngine
from zz.services.text import Text


class UndefinedVariableInTemplate(KeyError):
    pass


@deps.define
class AnatomyFile:
    """
    Implements a file.

    Usage:
        f = AnatomyFile('filename.txt', 'first line')
        f.apply('directory')
    """

    text = deps.Singleton(Text)

    filename: pathlib.Path = deps.field()
    content: str = deps.field()
    executable: bool = deps.field(default=False)

    def apply(self, directory, variables, filename=None):
        """
        Create the file using all registered blocks.
        Expand variables in all blocks.

        :param directory:
        :param variables:
        :return:
        """
        import functools

        expand = functools.partial(
            TemplateEngine.run, recursive_expansion=True, trim_blocks=True
        )

        filename = filename or self.filename
        filename = os.path.join(directory, filename)
        filename = expand(filename, variables)

        if self.content.startswith("!"):
            content_filename = self.content[1:]
            template_filename = "{{ ANATOMY.templates_dir }}/{{ ANATOMY.template}}"
            template_filename = f"{template_filename}/{content_filename}"
            template_filename = expand(template_filename, variables)
            content_filename = expand(template_filename, variables)
            self.content = open(content_filename).read()

        # Use alternative variable/block expansion when working with Ansible
        # file.
        alt_expansion = (
            filename.endswith("ansible.yml") or ".github/workflows" in filename
        )

        try:
            content = expand(self.content, variables, alt_expansion)
        except Exception as e:
            raise RuntimeError("ERROR: {}: {}".format(filename, e))

        self._create_file(filename, content)
        if self.executable:
            AnatomyFile.make_executable(filename)

    def _create_file(self, filename, contents):
        contents = contents.replace(" \n", "\n")
        contents = contents.rstrip("\n")
        contents += "\n"
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        try:
            with open(filename, "w") as oss:
                oss.write(contents)
        except Exception as e:
            raise RuntimeError(e)

    @staticmethod
    def make_executable(path):
        mode = os.stat(path).st_mode
        mode |= (mode & 0o444) >> 2  # copy R bits to X
        os.chmod(path, mode)


@deps.define
class AnatomySymlink:

    filename: pathlib.Path = deps.field()
    symlink: str = deps.field()
    executable: bool = deps.field(default=False)

    def apply(self, directory, variables, filename=None):
        """
        Create the file using all registered blocks.
        Expand variables in all blocks.

        :param directory:
        :param variables:
        :return:
        """
        import functools

        expand = functools.partial(
            TemplateEngine.run, recursive_expansion=True, trim_blocks=True
        )

        filename = filename or self.filename
        filename = os.path.join(directory, filename)
        filename = expand(filename, variables)

        symlink = os.path.join(os.path.dirname(filename), self.symlink)
        assert os.path.isfile(
            symlink
        ), "Can't find symlink destination file: {}".format(symlink)

        self._create_symlink(filename, symlink)
        if self.executable:
            AnatomyFile.make_executable(filename)

    @staticmethod
    def _create_symlink(filename, symlink):

        os.makedirs(os.path.dirname(filename), exist_ok=True)
        try:
            if os.path.isfile(filename) or os.path.islink(filename):
                os.unlink(filename)

            # Create a symlink with a relative path (not absolute)
            path = os.path.normpath(symlink)
            start = os.path.normpath(os.path.dirname(filename))
            symlink = os.path.relpath(path, start)

            os.symlink(symlink, filename)
        except Exception as e:
            raise RuntimeError(e)


@deps.define
class AnatomyTree:
    """
    A collection of anatomy-files.

    Usage:
        tree = AnatomyTree()
        tree.create_file('gitignore', '.gitignore', '.pyc')
        tree.apply('directory')
    """

    file_factory = deps.Factory(AnatomyFile)
    symlink_factory = deps.Factory(AnatomySymlink)

    _variables = deps.Attribute(OrderedDict)
    _files = deps.Attribute(dict)

    def get_file(self, filename):
        """
        Returns a AnatomyFile instance associated with the given filename, creating one if there's none registered.

        :param str filename:
        :return AnatomyFile:
        """
        result = self._files.get(filename, None)
        if result is None:
            result = self.file_factory(filename)
            self._files[filename] = result
        return result

    def apply(self, directory, variables=None):
        """
        Create all registered files.

        :param str directory:
        :param dict variables:
        """
        dd = self._variables.copy()
        if variables is not None:
            dd = merge_dict(dd, variables)

        for i_fileid, i_file in self._files.items():
            try:
                filename = dd[i_fileid]["filename"]
            except KeyError:
                filename = None
            i_file.apply(directory, variables=dd, filename=filename)

    def create_file(self, filename, contents, executable=False):
        """
        Create a new file in this tree.

        :param str filename:
        :param str contents:
        """
        if filename in self._files:
            raise FileExistsError(filename)

        self._files[filename] = self.file_factory(
            filename, contents, executable=executable
        )

    def create_link(self, filename, symlink, executable=False):
        """
        Create a new symlink in this tree.

        :param str filename:
        :param str symlink:
        """
        if filename in self._files:
            raise FileExistsError(filename)

        self._files[filename] = self.symlink_factory(
            filename, symlink, executable=executable
        )

    def add_variables(self, variables, left_join=True):
        """
        Adds the given variables to this tree variables.

        :param dict variables:
        :param bool left_join:
            If True, the root keys of the new variables (variables parameters) must already exist in the current
            variables dictionary.
        """
        self._variables = merge_dict(self._variables, variables, left_join=left_join)

    def evaluate(self, text):
        return eval(text, self._variables)


def merge_dict(d1, d2, left_join=True):
    """

    :param dict d1:
    :param dict d2:
    :return:
    """
    return _merge_dict(d1, d2, depth=0, left_join=left_join)


def _merge_dict(d1, d2, depth=0, left_join=True):
    def merge_value(v1, v2, override=False):
        if v2 is None:
            return v1
        elif override:
            return v2
        elif isinstance(v1, dict):
            return _merge_dict(v1, v2, depth=depth + 1, left_join=left_join)
        elif isinstance(v1, (list, tuple)):
            return v1 + v2
        else:
            return v2

    assert isinstance(d1, dict), "Parameter d1 must be a dict, not {}. d1={}".format(
        d1.__class__, d1
    )
    assert isinstance(d2, dict), "Parameter d2 must be a dict, not {}. d2={}".format(
        d2.__class__, d2
    )

    d2_cleaned = {i.rstrip("!"): j for (i, j) in d2.items()}

    if left_join and depth < 2:
        keys = d1.keys()
        right_keys = set(d2_cleaned.keys())
        right_keys = right_keys.difference(set(d1.keys()))
        if right_keys:
            raise RuntimeError("Extra keys: {}".format(right_keys))
    else:
        keys = list(d1.keys()) + [i for i in d2_cleaned.keys() if i not in d1]

    result = OrderedDict()
    for i_key in keys:
        try:
            result[i_key] = merge_value(
                d1.get(i_key), d2_cleaned.get(i_key), override=i_key + "!" in d2
            )
        except AssertionError as e:
            print("While merging value for key {}".format(i_key))
            raise e
    return result
