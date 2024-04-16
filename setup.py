#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import setup

setup(
    name='zops',
    use_scm_version=True,

    author="Alexandre Andrade",
    author_email='kaniabi@gmail.com',

    url='https://github.com/zerotk/zops',

    description="Command line operations.",
    long_description="Command line operations.",

    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.11',
    ],
#    keywords='development environment, shell, operations',

#    include_package_data=True,
#    packages=['zerotk', 'zerotk.zops'],
#    namespace_packages=['zerotk'],
    entry_points={
        'console_scripts': [
            'zops=zops.__main__:main',
            'zz=zz.__main__:main',
        ]
    },

    install_requires=[
        'click',
        # AWS
        "boto3",
        "tabulate",
        "pyyaml",
        "addict",
        # Anatomy
        "ansible",  # Just to use the filter 'combine'.
        "jinja2",
        "stringcase",
    ],
    setup_requires=['setuptools_scm'],
    tests_require=[
        "pytest",
        "datadiff",
    ],
    license="MIT license",
)
