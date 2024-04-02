from zops.anatomy.layers.feature import AnatomyFeatureRegistry
from zerotk.lib.yaml import yaml_from_file

from collections import OrderedDict


class AnatomyPlaybook(object):
    """
    Describes features and variables to apply in a project tree.
    """

    def __init__(self, condition=True):
        self.__features = OrderedDict()
        self.__variables = {}

    @classmethod
    def get_template_name(cls, filename):
        contents = yaml_from_file(filename)
        return contents.pop("anatomy-template", "application")

    @classmethod
    def from_file(cls, filename):
        contents = yaml_from_file(filename)
        result = cls.from_contents(contents)
        return result

    @classmethod
    def from_contents(cls, contents):
        result = cls()
        result.__use_feature("ANATOMY", [])
        contents = contents.pop("anatomy-playbook", contents)
        use_features = contents.pop("use-features")
        if not isinstance(use_features, dict):
            raise TypeError(
                'Use-features must be a dict not "{}"'.format(use_features.__class__)
            )
        skip_features = contents.pop("skip-features", [])
        for i_feature_name, i_variables in use_features.items():
            result.__use_feature(i_feature_name, skip_features)
            i_variables = cls._process_variables(i_variables)
            result.set_variables(i_feature_name, i_variables)

        if contents.keys():
            raise KeyError(list(contents.keys()))

        return result

    @classmethod
    def _process_variables(cls, variables):
        return variables

    def __use_feature(self, feature_name, skipped):
        feature = AnatomyFeatureRegistry.get(feature_name)
        feature.using_features(self.__features, skipped)

    def set_variables(self, feature_name, variables):
        """
        :param str key:
        :param object value:
        """
        assert feature_name not in self.__variables
        self.__variables[feature_name] = variables

    def apply(self, directory):
        from zops.anatomy.layers.tree import AnatomyTree
        import os

        tree = AnatomyTree()

        if not os.path.isdir(directory):
            os.makedirs(directory)

        print("Applying features:")
        for i_feature_name, i_feature in self.__features.items():
            i_feature.apply(tree)
            print(" * {}".format(i_feature_name))

        print("Applying anatomy-tree.")
        tree.apply(directory, self.__variables)
