from collections import OrderedDict
from dataclasses import dataclass


class FeatureNotFound(KeyError):
    pass


class FeatureAlreadyRegistered(KeyError):
    pass


class AnatomyFeatureRegistry(object):

    feature_registry = OrderedDict()

    @classmethod
    def clear(cls):
        cls.feature_registry = OrderedDict()

    @classmethod
    def get(cls, feature_name):
        """
        Returns a previously registered feature associated with the given feature_name.

        :param str feature_name:
        :return AnatomyFeature:
        """
        try:
            return cls.feature_registry[feature_name]
        except KeyError:
            raise FeatureNotFound(feature_name)

    @classmethod
    def register(cls, feature_name, feature):
        """
        Registers a feature instance to a name.

        :param str feature_name:
        :param AnatomyFeature feature:
        """
        if feature_name in cls.feature_registry:
            raise FeatureAlreadyRegistered(feature_name)
        cls.feature_registry[feature_name] = feature

    @classmethod
    def register_from_file(cls, filename, templates_dir):
        from zerotk.lib.yaml import yaml_from_file

        contents = yaml_from_file(filename)
        return cls.register_from_contents(contents, templates_dir)

    @classmethod
    def register_from_text(cls, text):
        from zerotk.lib.yaml import yaml_load
        from zerotk.lib.text import dedent

        text = dedent(text)
        contents = yaml_load(text)
        return cls.register_from_contents(contents, templates_dir="")

    @classmethod
    def register_from_contents(cls, contents, templates_dir):
        feature = AnatomyFeature.from_contents(
            {
                "name": "ANATOMY",
                "variables": {
                    "templates_dir": templates_dir,
                    "template": "application",
                },
            },
        )
        cls.register(feature.name, feature)

        for i_feature in contents["anatomy-features"]:
            feature = AnatomyFeature.from_contents(i_feature)
            cls.register(feature.name, feature)

    @classmethod
    def tree(cls):
        """
        Returns all files created by the registered features.

        This is part of the helper functions for the end-user. Since the user must know all the file-ids in order to add
        contents to the files we'll need a way to list all files and their IDs.

        :return 3-tupple(str, str, str):
            Returns a tuple containing:
                [0]:    Feature name
                [1]:    File-id
                [2]:    Filename
        """
        result = []
        for i_name, i_feature in cls.feature_registry.items():
            for j_filename in i_feature.filenames():
                result.append((i_name, j_filename, j_filename))
        return result


class IAnatomyFeature(object):
    """
    Implements a feature. A feature can add content in many files in its 'apply' method.

    Usage:
        tree = AnatomyTree()
        variables = {}

        feature = AnatomyFeatureRegistry.get('alpha')
        feature.apply(tree, variables)

        tree.apply('directory')
    """

    def __init__(self, name):
        self.__name = name

    @property
    def name(self):
        return self.__name

    def apply(self, tree):
        """
        Apply this feature instance in the given anatomy-tree.

        :param AnatomyTree tree:
        """
        raise NotImplementedError()


class AnatomyFeature(IAnatomyFeature):

    @dataclass
    class File:
        filename: str
        contents: str
        symlink: str
        executable: bool

    def __init__(self, name, variables=None, use_features=None, condition="True"):
        super().__init__(name)
        self.__condition = condition
        self.__variables = OrderedDict()
        self.__variables[name] = variables or OrderedDict()
        self.__use_features = use_features or OrderedDict()
        self.__enabled = True
        self.__files = []

    def is_enabled(self):
        return self.__enabled

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
        result = AnatomyFeature(name, variables, use_features, condition=condition)
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

    @property
    def filename(self):
        raise NotImplementedError()

    def apply(self, tree):
        """
        Implements AnatomyFeature.apply.
        """
        tree.add_variables(self.__use_features, left_join=True)
        tree.add_variables(self.__variables, left_join=False)

        result = self.is_enabled()
        if result and self.__files:
            for i_file in self.__files:
                if i_file.contents:
                    tree.create_file(
                        i_file.filename, i_file.contents, executable=i_file.executable
                    )
                else:
                    tree.create_link(
                        i_file.filename, i_file.symlink, executable=i_file.executable
                    )
        return result

    def using_features(self, features, skipped):
        self.__enabled = self.name not in skipped
        for i_name, i_vars in self.__use_features.items():
            feature = AnatomyFeatureRegistry.get(i_name)
            feature.using_features(features, skipped)
        # DEBUGGING: print('using anatomy-feature {} ({})'.format(self.name, id(self)))
        feature = features.get(self.name)
        if feature is None:
            features[self.name] = self
        else:
            assert id(feature) == id(self)

    def create_file(self, filename, contents, executable=False):
        self.__files.append(
            self.File(
                filename = filename,
                contents = contents,
                symlink = None,
                executable = executable
            )
        )

    def create_link(self, filename, symlink, executable=False):
        self.__files.append(
            self.File(
                filename = filename,
                contents=None,
                symlink=symlink,
                executable=executable
            )
        )

    def filenames(self):
        return [i.filename for i in self.__files]
