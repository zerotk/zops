def sort_version_tags(versions):
    from semantic_version import Version

    result = sorted([Version(i.lstrip("v"), partial=True) for i in versions])
    return list(map(str, result))
