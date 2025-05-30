from zerotk import deps
from zz.anatomy.layers.playbook import AnatomyPlaybook
from zz.anatomy.layers.registry import AnatomyFeatureRegistry
from zz.services.console import Console
from zz.services.filesystem import FileSystem


@deps.define
class AnatomyEngine:

    filesystem = deps.Singleton(FileSystem)
    console = deps.Singleton(Console)

    registry_factory = deps.Factory(AnatomyFeatureRegistry)
    playbook_factory = deps.Factory(AnatomyPlaybook)

    def run(self, directory):
        playbooks = self.filesystem.Path(directory).rglob("anatomy-playbook.yml")
        for i_playbook in playbooks:
            self._apply_anatomy(i_playbook)

    def _apply_anatomy(self, playbook_filename):
        self.console.info(f"Playbook {playbook_filename}")

        features_filename = self._find_features(playbook_filename)
        templates_dir = features_filename.parent / "templates"
        self.console.info(f"Features {features_filename}")

        registry = self.registry_factory()
        # print("OUTSIDE", id(registry), id(registry._items))
        registry.from_file(features_filename, templates_dir)
        playbook = self.playbook_factory(registry=registry)
        playbook.from_file(playbook_filename)
        playbook.apply(playbook_filename.parent)

    def _find_features(self, playbook_filename):
        import pathlib

        from zerotk.path import find_up
        from zz.services.console import Console

        SEARCH_FILENAMES = [
            pathlib.Path("anatomy-features/anatomy-features.yml"),
            pathlib.Path("anatomy-features.yml"),
        ]

        for i_filename in SEARCH_FILENAMES:
            result = find_up(i_filename, playbook_filename.parent)
            if result is not None:
                break

        if result is None:
            Console.error("Can't find features file: anatomy-features.yml.")
            raise SystemError(1)

        return pathlib.Path(result)

    def _register_features(self, filename, templates_dir):
        from zz.anatomy.layers.feature import AnatomyFeatureRegistry

        AnatomyFeatureRegistry.clear()
        AnatomyFeatureRegistry.register_from_file(filename, templates_dir)
