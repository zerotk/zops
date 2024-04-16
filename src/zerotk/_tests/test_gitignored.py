def test_gitignored_filter(datadir):
    from zerotk.lib.gitignored import GitIgnored

    gitignored = GitIgnored(git_directory="git-root.txt")

    filenames = [
        datadir / "test_00/ignored/alpha.txt",
        datadir / "test_00/included/alpha.txt",
    ]

    assert gitignored.filter(filenames) == [datadir / "test_00/included/alpha.txt"]


def test_gitignored_list(datadir):
    from zerotk.lib.gitignored import GitIgnored

    gitignored = GitIgnored(git_directory="git-root.txt")

    assert gitignored.list(datadir / "test_00/ignored/alpha.txt") == [
        datadir / "test_00/.gitignore"
    ]


# def test_gitignored_match_pattern():
#     from zerotk.lib.gitignored import GitIgnored
#
#     gitignored = GitIgnored(
#         git_directory='git-root.txt',
#     )
#
#     # Pattern 'ignored'
#     # * should match anything that matches ignored
#     pattern = 'ignored'
#     assert gitignored.match_pattern('/ignored/zulu.txt', '/', pattern)
#     assert gitignored.match_pattern('/alpha/ignored/zulu.txt', '/', pattern)
#     assert gitignored.match_pattern('/alpha/bravo/ignored/zulu.txt', '/', pattern)
#
#     # Pattern '*.ignored'
#     # * should match files and directorys that have the .ignore extension
#     pattern = '*.ignored'
#     assert gitignored.match_pattern('/alpha.ignored', '/', pattern)
#     assert not gitignored.match_pattern('/ignored/zulu.txt', '/', pattern)
#     assert not gitignored.match_pattern('/alpha/ignored/zulu.txt', '/', pattern)
#     assert not gitignored.match_pattern('/alpha/ignored', '/', pattern)
#
#     # Pattern /ignored_root_dir/
#     # * should ignore only if at the root directory AND it is a directory.
#     pattern = '/ignored_root_dir/'
#     assert gitignored.match_pattern('/ignored_root_dir', '/', pattern)
#     assert not gitignored.match_pattern('/alpha/ignored_root_dir', '/', pattern)
