import re
import os.path
from setuptools import setup, find_packages
from setuptools.command import build_ext
from setuptools.command.install_lib import install_lib
import subprocess
import shutil
import pkg_resources


CONF_DIR = '/etc/vap'
LOG_DIR = '/var/log/vap'


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


class PostInstall(install_lib):
    def run(self):
        global CONF_DIR
        global LOG_DIR
        # Call parent
        install_lib.run(self)
        # Execute commands
        if not os.path.exists(CONF_DIR):
            os.makedirs(CONF_DIR)
        if not os.path.exists(LOG_DIR):
            os.makedirs(LOG_DIR)

        path = pkg_resources.resource_filename(__name__, 'data/sysagentd.cfg')
        shutil.copy(path, os.path.join(CONF_DIR, 'sysagentd.cfg'))


COMMAND_CLASS = {
        'build_ext': BuildExt,
        'install_lib': PostInstall,
        }
LICENSE = 'BSD'
CLASSIFIERS = [
        'Development Status :: 5 - Production/Stable',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        ]
INSTALL_REQUIRES = (
        "protobuf",
        "grpcio",
        )

with open(
    os.path.join(os.path.dirname(__file__), 'sysagent', '__init__.py')
    ) as f:
    VERSION = re.match(r".*__version__ = '(.*?)'", f.read(), re.S).group(1)
with open(
    os.path.join(os.path.dirname(__file__), 'README.md')
    ) as f:
    DESCRIPION = f.read()

setup(
    name='sysagent',
    version=VERSION,
    description='A gRPC server for system',
    long_description=DESCRIPION,
    author='anymous',
    author_email='anymous@example.com',
    packages=find_packages(),
    data_files=[('data', ['data/sysagentd.cfg'])],
    license=LICENSE,
    classifiers=CLASSIFIERS,
    install_requires=INSTALL_REQUIRES,
    python_requires='>=3',
    url='www.example.com',
    cmdclass=COMMAND_CLASS,
    entry_points={
        'console_scripts': [
            'sys-agentd=sysagent.sysagentd:Main'
        ],
    }
)
