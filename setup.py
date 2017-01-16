#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import setup

setup(
    name='zerotk.zops',
    use_scm_version=True,

    author="Alexandre Andrade",
    author_email='kaniabi@gmail.com',

    url='https://github.com/zerotk/zops',

    description="Extensible command line operations for software development.",
    long_description="Extensible command line operations for software development.",

    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
    ],
    keywords='development environment, shell, operations',

    include_package_data=True,
    packages=['zerotk', 'zerotk.zops'],
    namespace_packages=['zerotk'],
    entry_points={
        'console_scripts': [
            'zops=zerotk.zops.cli:main'
        ]
    },

    install_requires=[
        'click',
        'click-plugins',
    ],
    setup_requires=['setuptools_scm'],
    tests_require=[],

    license="MIT license",
)
