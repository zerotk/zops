from collections import OrderedDict
from zerotk import deps
from zerotk.yaml import yaml_from_file
from .registry import AnatomyFeatureRegistry
from .tree import AnatomyTree
import pathlib


@deps.define
class AnatomyPlaybook:
    """
    Describes features and variables to apply in a project tree.
    """

    tree_factory = deps.Factory(AnatomyTree)

    registry: AnatomyFeatureRegistry = deps.field()
    _features = deps.Attribute(OrderedDict)
    _variables = deps.Attribute(dict)

    # @classmethod
    # def get_template_name(cls, filename):
    #     contents = yaml_from_file(filename)
    #     return contents.pop("anatomy-template", "application")

    def from_file(self, filename: pathlib.Path) -> None:
        contents = yaml_from_file(filename)
        self.from_contents(contents)

    def from_contents(self, contents: str) -> None:
        # Always add ANATOMY feature to the list of features for the playbook.
        self._add_feature("ANATOMY")
        contents = contents.pop("anatomy-playbook", contents)
        use_features = contents.pop("use-features")
        if not isinstance(use_features, dict):
            raise TypeError(
                f"Use-features must be a dict not '{use_features.__class__}'"
            )
        skip_features = contents.pop("skip-features", [])
        for i_feature_name, i_variables in use_features.items():
            self._add_feature(i_feature_name, skip_features)
            self._add_variables(i_feature_name, self._process_variables(i_variables))

        if contents.keys():
            raise KeyError(list(contents.keys()))

    def _process_variables(self, variables):
        return variables

    def _add_feature(self, feature_name, skip_features=[]):
        # print("INSIDE", id(self._features), len(self._features))
        feature = self.registry.get(feature_name)

        # Check if we already loaded a feature with the same name and if that's the case check if
        # it's the same instance.
        check_feature = self._features.get(feature_name)
        if check_feature is not None:
            assert id(check_feature) == id(feature)
            return

        feature.enabled = feature.name not in skip_features
        for i_name in feature.use_features:
            self._add_feature(i_name, skip_features)

        self._features[feature_name] = feature

    def _add_variables(self, feature_name, variables):
        assert feature_name not in self._variables
        self._variables[feature_name] = variables

    def apply(self, directory):
        import os

        tree = self.tree_factory()

        if not os.path.isdir(directory):
            os.makedirs(directory)

        print("Applying features:")
        for i_feature_name, i_feature in self._features.items():
            i_feature.apply(tree)
            print(" * {}".format(i_feature_name))

        print("Applying anatomy-tree.")
        tree.apply(directory, self._variables)
