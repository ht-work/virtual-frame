#!/usr/bin/env python
# encoding: utf-8

from setuptools import setup, find_packages

setup(
    name = 'netcopy',
    version = '0.9',
    keywords = ('vap', 'vik', 'virtualization'),
    description = 'remote file copy utils',
    long_description = 'remote file copy utils for vik/vim',

    packages = find_packages('src', exclude=['tests']),
    package_dir = {'':'src'},
    include_package_data = True,
    platforms = 'x86-64, aarch64',
    install_requires = [],

    scripts = [],
    entry_points={
        'console_scripts': [
            'ncp-server=netcp.filetools:ServerMain',
            'ncp-client=netcp.filetools:ClientMain'
        ]
    }
)
