#!/usr/bin/env python
# encoding: utf-8

from setuptools import setup, find_packages

setup(
    name = 'virt_agent',
    version = '0.9',
    keywords = ('vap', 'vik', 'virtualization'),
    description = 'virt_agent',
    long_description = 'virt_agent for vik',

    packages = find_packages('src', exclude=['tests']),
    package_dir = {'':'src'},
    include_package_data = True,
    platforms = 'x86-64, aarch64',
    install_requires = [],

    scripts = [],

    entry_points = {
        'console_scripts' : [
            'virt_agentd = virt_agent.virt_agentd:main',
            'virt_agent_cli = virt_agent.virt_agentd:main_cli',
        ]
    }
)
