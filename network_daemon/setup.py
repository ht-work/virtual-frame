import re
import os.path
import shutil
import setuptools
import pkg_resources
from setuptools import setup, find_packages
from setuptools.command import build_ext
import subprocess
from setuptools.command.install_lib import install_lib

CONF_DIR = '/etc/vap'
NET_AGENT_ACL_CONF_DIR = '/opt/vap/net_agent/acl'
NET_AGENT_QOS_CONF_DIR = '/opt/vap/net_agent/qos'
NET_AGENT_LOG_DIR = '/var/log/vap'


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
        if not os.path.exists(NET_AGENT_ACL_CONF_DIR):
            os.makedirs(NET_AGENT_ACL_CONF_DIR)
        if not os.path.exists(NET_AGENT_QOS_CONF_DIR):
            os.makedirs(NET_AGENT_QOS_CONF_DIR)
        if not os.path.exists(NET_AGENT_LOG_DIR):
            os.makedirs(NET_AGENT_LOG_DIR)
        path = pkg_resources.resource_filename(__name__, 'net_agent.cfg')
        shutil.copy(path, os.path.join(CONF_DIR, 'net_agent.cfg'))

COMMAND_CLASS = {
        'build_ext': BuildExt,
        "install_lib": post_install
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
        "psutil",
        )

with open(
    os.path.join(os.path.dirname(__file__), 'net_agent', '__init__.py')
    ) as f:
    VERSION = re.match(r".*__version__ = '(.*?)'", f.read(), re.S).group(1)

with open(
    os.path.join(os.path.dirname(__file__), 'README.md')
    ) as f:
    DESCRIPION = f.read()

setup(
    name='net_agentd',
    version=VERSION,
    description='net_agentd gRPC server for VIK',
    long_description=DESCRIPION,
    author='xuminyuan',
    author_email='xuminyuan@163.com',
    packages=find_packages(),
    license=LICENSE,
    classifiers=CLASSIFIERS,
    install_requires=INSTALL_REQUIRES,
    python_requires='>=3',
    url='www.k.cn',
    cmdclass=COMMAND_CLASS,
    package_data={'':['../net_agent.cfg']},
    entry_points={
        'console_scripts': [
            'net_agentd=net_agent.net_agentd:main'
        ],
    }
)

