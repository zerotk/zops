import pytest


class _EmbedDataFixture(object):

    def __init__(self, request):
        from zerotk.easyfs import StandardizePath

        module_name = request.module.__name__.split(".")[-1]

        # source directory: same name as the name of the test's module
        self._source_dir = request.fspath.dirname + "/" + module_name

        # data-dir directory: same name as the name of the test's module
        data_dir_basename = module_name.replace("test_", "data_")
        data_dir_basename = data_dir_basename.replace("_test", "_data")

        self._data_dir = StandardizePath(
            request.fspath.dirname
            + "/"
            + data_dir_basename
            + "-"
            + request.function.__name__
        )

    def create_data_dir(self):
        from zerotk.easyfs import CopyDirectory
        from zerotk.easyfs import CreateDirectory
        from zerotk.easyfs import IsDir

        if IsDir(self._source_dir):
            CopyDirectory(self._source_dir, self._data_dir, override=False)
        else:
            CreateDirectory(self._data_dir)

    def delete_data_dir(self):
        from zerotk.easyfs import DeleteDirectory
        from zerotk.easyfs import IsDir

        if IsDir(self._data_dir):
            DeleteDirectory(self._data_dir)

    def get_data_dir(self):
        """
        :rtype: unicode
        :returns:
            Returns the absolute path to data-directory name to use, standardized by StandardizePath.

        @remarks:
            This method triggers the data-directory creation.
        """
        return self._data_dir

    def get_filename(self, *parts):
        """
        Returns an absolute filename in the data-directory (standardized by StandardizePath).

        @params parts: list(unicode)
            Path parts. Each part is joined to form a path.

        :rtype: unicode
        :returns:
            The full path prefixed with the data-directory.

        @remarks:
            This method triggers the data-directory creation.
        """
        from zerotk.easyfs import StandardizePath

        result = [self._data_dir] + list(parts)
        result = "/".join(result)
        return StandardizePath(result)

    def __getitem__(self, index):
        return self.get_filename(index)

    def assert_equal_files(
        self,
        obtained_fn,
        expected_fn,
        fix_callback=lambda x: x,
        binary=False,
        encoding=None,
    ):
        """
        Compare two files contents. If the files differ, show the diff and write a nice HTML
        diff file into the data directory.

        Searches for the filenames both inside and outside the data directory (in that order).

        :param unicode obtained_fn: basename to obtained file into the data directory, or full path.

        :param unicode expected_fn: basename to expected file into the data directory, or full path.

        :param bool binary:
            Thread both files as binary files.

        :param unicode encoding:
            File's encoding. If not None, contents obtained from file will be decoded using this
            `encoding`.

        :param callable fix_callback:
            A callback to "fix" the contents of the obtained (first) file.
            This callback receives a list of strings (lines) and must also return a list of lines,
            changed as needed.
            The resulting lines will be used to compare with the contents of expected_fn.

        :param bool binary:
            .. seealso:: zerotk.easyfs.GetFileContents
        """
        import os

        from zerotk.easyfs import GetFileContents
        from zerotk.easyfs import GetFileLines

        __tracebackhide__ = True
        import io

        def FindFile(filename):
            # See if this path exists in the data dir
            data_filename = self.get_filename(filename)
            if os.path.isfile(data_filename):
                return data_filename

            # If not, we might have already received a full path
            if os.path.isfile(filename):
                return filename

            # If we didn't find anything, raise an error
            from ._exceptions import MultipleFilesNotFound

            raise MultipleFilesNotFound([filename, data_filename])

        obtained_fn = FindFile(obtained_fn)
        expected_fn = FindFile(expected_fn)

        if binary:
            obtained_lines = GetFileContents(obtained_fn, binary=True)
            expected_lines = GetFileContents(expected_fn, binary=True)
            assert obtained_lines == expected_lines
        else:
            obtained_lines = fix_callback(GetFileLines(obtained_fn, encoding=encoding))
            expected_lines = GetFileLines(expected_fn, encoding=encoding)

            if obtained_lines != expected_lines:
                html_fn = os.path.splitext(obtained_fn)[0] + ".diff.html"
                html_diff = self._generate_html_diff(
                    expected_fn, expected_lines, obtained_fn, obtained_lines
                )
                with io.open(html_fn, "w") as f:
                    f.write(html_diff)

                import difflib

                diff = ["FILES DIFFER:", obtained_fn, expected_fn]
                diff += ["HTML DIFF: %s" % html_fn]
                diff += difflib.context_diff(obtained_lines, expected_lines)
                raise AssertionError("\n".join(diff) + "\n")

    def _generate_html_diff(
        self, expected_fn, expected_lines, obtained_fn, obtained_lines
    ):
        """
        Returns a nice side-by-side diff of the given files, as a string.

        """
        import difflib

        differ = difflib.HtmlDiff()
        return differ.make_file(
            fromlines=expected_lines,
            fromdesc=expected_fn,
            tolines=obtained_lines,
            todesc=obtained_fn,
        )


@pytest.yield_fixture
def embed_data(request):
    """
    Create a temporary directory with input data for the test.
    The directory contents is copied from a directory with the same name as the module located in the same directory of
    the test module.
    """
    result = _EmbedDataFixture(request)
    result.delete_data_dir()
    result.create_data_dir()
    yield result
    result.delete_data_dir()
