from functools import lru_cache
import logging


class GitIgnored(object):
    """
    Helper class to find out if a filename is being ignored by .gitignore files.
    """

    def __init__(self, git_directory=".git", gitignore_filename=".gitignore"):
        self.__gitignore_filename = gitignore_filename
        self.__git_directory = git_directory
        self._logger = logging.getLogger(__name__)

    def filter(self, filenames):
        """
        Filters filenames that match .gitignore files in their parent path.

        :param list(Path) filenames:
        :return list(Path):
        """
        from pathlib import Path

        filenames = map(Path, filenames)
        return [i for i in filenames if not self.is_ignored(i)]

    def is_ignored(self, filename):
        """
        Returns whether the given filename is git-ignored considering all .gitignore files in their parent path.

        :param Path filename:
        :return bool:
        """
        from pathspec import PathSpec
        from pathspec.patterns import GitWildMatchPattern

        self._logger.debug("is_ignored", filename)
        patterns = self._collect_patterns(filename)
        self._logger.debug("patterns", patterns)
        spec = PathSpec(map(GitWildMatchPattern, patterns))
        result = spec.match_file(str(filename))

        return result

    def _collect_patterns(self, filename):
        """
        Collect patterns from all .gitignore files in the parent path.

        :param Path filename:
        :return list(str):
        """
        from pathlib import Path

        result = []

        filename = Path(filename).resolve()

        for i_filename in self.list(filename):
            self._logger.debug("_collect_patterns", i_filename)
            result += self._read_patterns(i_filename)

        return result

    @lru_cache()
    def _read_patterns(self, filename):
        """
        Returns a list of patterns from the given filename.

        :param Path filename:
        :return list(str):
        """
        result = filename.read_text().split("\n")
        result = [i.strip() for i in result]
        result = [i for i in result if len(i) > 0]
        self._logger.debug("_read_patterns", result)
        return result

    def list(self, filename):
        """
        Lists all gitignore files that have influence to the given filename.

        Stops when it finds the repository root directory, in other words, when it finds the directory with a .git directory
        in it.

        :param Path filename:
        :return list(Path):
        """
        from pathlib import Path

        result = []

        curdir = Path(filename)
        while curdir != curdir.root:
            gitignore = curdir / self.__gitignore_filename
            if gitignore.exists():
                result.append(gitignore)

            if self._is_git_root(curdir):
                break

            curdir = curdir.parent

        return result

    def _is_git_root(self, directory):
        """
        Returns wheter the given directory is the root directory of a Git repository.

        :param Path directory:
        :return bool:
        """
        git_filename = directory / self.__git_directory
        return git_filename.exists()
