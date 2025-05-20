from collections import OrderedDict

from zerotk import deps

from .feature import AnatomyFeature


class FeatureNotFound(KeyError):
    pass


class FeatureAlreadyRegistered(KeyError):
    pass


@deps.define
class AnatomyFeatureRegistry:

    _items = deps.Attribute(OrderedDict)

    def from_file(self, filename, templates_dir):
        from zerotk.yaml import yaml_from_file

        contents = yaml_from_file(filename)
        return self.from_contents(contents, templates_dir)

    def from_text(self, text):
        from zerotk.text import dedent
        from zerotk.yaml import yaml_load

        text = dedent(text)
        contents = yaml_load(text)
        return self.from_contents(contents, templates_dir="")

    def from_contents(self, contents, templates_dir):
        feature = AnatomyFeature.from_contents(
            {
                "name": "ANATOMY",
                "variables": {
                    "templates_dir": templates_dir,
                    "template": "application",
                },
            },
        )
        self.register(feature.name, feature)

        for i_feature in contents["anatomy-features"]:
            feature = AnatomyFeature.from_contents(i_feature)
            self.register(feature.name, feature)

    def get(self, feature_name):
        """
        Returns a previously registered feature associated with the given feature_name.

        :param str feature_name:
        :return AnatomyFeature:
        """
        try:
            return self._items[feature_name]
        except KeyError:
            raise FeatureNotFound(feature_name)

    def register(self, feature_name, feature):
        """
        Registers a feature instance to a name.

        :param str feature_name:
        :param AnatomyFeature feature:
        """
        if feature_name in self._items:
            raise FeatureAlreadyRegistered(feature_name)
        # print("REGISTER", id(self), len(self._items))
        self._items[feature_name] = feature

    def tree(self):
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
        for i_name, i_feature in self._items.items():
            for j_filename in i_feature.filenames():
                result.append((i_name, j_filename, j_filename))
        return result
