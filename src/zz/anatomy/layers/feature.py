from collections import OrderedDict
from dataclasses import dataclass


class AnatomyFeature:

    @dataclass
    class File:
        filename: str
        contents: str
        symlink: str
        executable: bool

    @classmethod
    def from_contents(cls, contents):
        def optional_pop(dd, key, default):
            try:
                return dd.pop(key)
            except KeyError:
                return default

        name = contents.pop("name")
        condition = contents.pop("condition", "True")
        variables = contents.pop("variables", OrderedDict())
        use_features = contents.pop("use-features", None)
        result = cls(name, variables, use_features, condition=condition)
        create_files = contents.pop("create-files", [])

        create_file = contents.pop("create-file", None)
        if create_file is not None:
            create_files.append(create_file)

        for i_create_file in create_files:
            symlink = optional_pop(i_create_file, "symlink", None)
            template = optional_pop(i_create_file, "template", None)
            filename = i_create_file.pop("filename", template)
            executable = optional_pop(i_create_file, "executable", False)
            if symlink is not None:
                result.create_link(filename, symlink, executable=executable)
            else:
                if template is not None:
                    file_contents = f"!{template}"
                else:
                    file_contents = i_create_file.pop("contents")
                result.create_file(filename, file_contents, executable=executable)

            if i_create_file.keys():
                raise KeyError(list(i_create_file.keys()))

        if contents.keys():
            raise KeyError(list(contents.keys()))

        return result

    def __init__(self, name, variables=None, use_features=None, condition="True"):
        self.name = name
        self.condition = condition
        self.variables = OrderedDict()
        self.variables[name] = variables or OrderedDict()
        self.use_features = use_features or OrderedDict()
        self.enabled = True
        self.files = []

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.name}>"

    @property
    def filename(self):
        raise NotImplementedError()

    def apply(self, tree):
        """
        Implements AnatomyFeature.apply.
        """
        tree.add_variables(self.use_features, left_join=True)
        tree.add_variables(self.variables, left_join=False)

        result = self.enabled
        if result and self.files:
            for i_file in self.files:
                if i_file.contents:
                    tree.create_file(
                        i_file.filename, i_file.contents, executable=i_file.executable
                    )
                else:
                    tree.create_link(
                        i_file.filename, i_file.symlink, executable=i_file.executable
                    )
        return result

    def create_file(self, filename, contents, executable=False):
        self.files.append(
            self.File(
                filename=filename,
                contents=contents,
                symlink=None,
                executable=executable,
            )
        )

    def create_link(self, filename, symlink, executable=False):
        self.files.append(
            self.File(
                filename=filename, contents=None, symlink=symlink, executable=executable
            )
        )

    def filenames(self):
        return [i.filename for i in self.files]
