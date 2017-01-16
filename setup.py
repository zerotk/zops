#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import setup

setup(
    name='zerotk.zops',
    version='0.1.0',
    description="Extensible command line operations for software development.",
    long_description="Extensible command line operations for software development.",
    author="Alexandre Andrade",
    author_email='kaniabi@gmail.com',
    url='https://github.com/zerotk/zops',
    packages=['zerotk', 'zerotk.zops'],
    namespace_packages=['zerotk'],
    entry_points={
        'console_scripts': [
            'zops=zerotk.zops.cli:main'
        ]
    },
    include_package_data=True,
    install_requires=[
        'click',
        'click-plugins',
    ],
    license="MIT license",
    zip_safe=False,
    keywords='development environment, shell, operations',
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
    test_suite='tests',
    tests_require=[]
)
