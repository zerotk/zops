from ruamel.yaml.constructor import DuplicateKeyError


def yaml_from_file(filename_):
    with open(filename_, "r") as iss:
        content = iss.read()
        result = yaml_load(content)
    return result


def yaml_load(text):
    from ruamel.yaml import YAML

    yaml = YAML()
    return yaml.load(text)


def yaml_load_key(filename, key):
    import os

    filename = os.path.expanduser(filename)

    if not os.path.isfile(filename):
        return None

    content = yaml_from_file(filename)
    return content.get(key, None)