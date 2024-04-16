import contextlib
import os


def find_all(name, path):
    result = []
    for root, dirs, files in os.walk(path):
        if name in files:
            result.append(os.path.join(root, name))
    return result


def find_up(name, path):
    directory = os.path.abspath(path)
    while directory:
        filename = os.path.join(directory, name)
        if os.path.exists(filename):
            return filename
        if directory == "/":
            raise FileNotFoundError("The file {} was not found".format(name))
        directory = os.path.dirname(directory)
    return None


@contextlib.contextmanager
def popd(dir):
    curdir = os.getcwd()
    try:
        os.chdir(dir)
        yield os.getcwd()
    finally:
        os.chdir(curdir)
