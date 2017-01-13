#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = [
    'Click>=6.0',
    'piptools',
]

test_requirements = [
    # TODO: put package test requirements here
]

setup(
    name='zerotk.operations',
    version='0.1.0',
    description="Extensible command line operations for software development.",
    long_description=readme + '\n\n' + history,
    author="Alexandre Andrade",
    author_email='kaniabi@gmail.com',
    url='https://github.com/Kaniabi/operations',
    packages=['zerotk', 'zerotk.operations'],
    namespace_packages=['zerotk'],
    # package_dir={'operations': 'operations'},
    entry_points={
        'console_scripts': [
            'zops=zerotk.operations.cli:main'
        ]
    },
    include_package_data=True,
    install_requires=requirements,
    license="MIT license",
    zip_safe=False,
    keywords='operations',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
    ],
    test_suite='tests',
    tests_require=test_requirements
)
