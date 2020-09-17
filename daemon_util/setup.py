#!/usr/bin/env python
# encoding: utf-8

import os.path
import shutil
import setuptools
import pkg_resources
from setuptools import setup, find_packages
from setuptools.command import build_ext
import subprocess
from setuptools.command.install_lib import install_lib


CONF_DIR = '/etc/vap'


class BuildExt(build_ext.build_ext):
    try:
        run_make = subprocess.Popen(['make', 'all'],
                                    stdin=subprocess.PIPE,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
        std_out, std_err = run_make.communicate()
        print(std_out.decode('utf-8'))
        if std_err:
            print(std_err.decode('utf-8'))
    except Exception as error:
        raise print('Failed build_ext step')

class post_install(install_lib):
    def run(self):
        # Call parent
        install_lib.run(self)
        # Execute commands
        if not os.path.exists(CONF_DIR):
            os.mkdir(CONF_DIR)
        path = pkg_resources.resource_filename(__name__, 'data/util_global.cfg')
        print("post_install path: %s" % path)
        shutil.copy(path, os.path.join(CONF_DIR, 'util_global.cfg'))

COMMAND_CLASS = {
        'build_ext': BuildExt,
        "install_lib": post_install
        }

setup(
    name = 'util_base',
    version = '0.9',
    keywords = ('vap', 'vik', 'virtualization'),
    description = 'basic utils',
    long_description = 'basic utils for vik',
    data_files=[('data', ['data/util_global.cfg'])],
    packages = find_packages('src', exclude=['tests']),
    package_dir = {'':'src'},
    include_package_data = True,
    platforms = 'x86-64, aarch64',
    install_requires = [],
    cmdclass=COMMAND_CLASS,
    scripts = [],
    entry_points={
        'console_scripts': [
            'direct-copy=util_base.direct_copy:main',
            'get-md5=util_base.get_md5:main',
        ]
    }

)
