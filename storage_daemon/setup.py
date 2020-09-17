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
STORE_AGENT_BASE_DIR = '/opt/storeagent'
STORE_AGENT_CONF_DIR = '/opt/storeagent/conf'
STORE_AGENT_XML_DIR = '/opt/storeagent/xml'
STORE_AGENT_JSON_DIR = '/opt/storeagent/json'
STORE_AGENT_LOG_DIR = '/var/log/vap'


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
        if not os.path.exists(STORE_AGENT_BASE_DIR):
            os.mkdir(STORE_AGENT_BASE_DIR)
        if not os.path.exists(STORE_AGENT_CONF_DIR):
            os.mkdir(STORE_AGENT_CONF_DIR)
        if not os.path.exists(STORE_AGENT_JSON_DIR):
            os.mkdir(STORE_AGENT_JSON_DIR)
        if not os.path.exists(STORE_AGENT_XML_DIR):
            os.mkdir(STORE_AGENT_XML_DIR)
        if not os.path.exists(STORE_AGENT_LOG_DIR):
            os.mkdir(STORE_AGENT_LOG_DIR)

        # copy
        cfg_path = pkg_resources.resource_filename(__name__, 'data/storeagent.cfg')
        shutil.copy(cfg_path, os.path.join(CONF_DIR, 'storeagent.cfg'))

        schema_path = pkg_resources.resource_filename(__name__, 'data/schema.json')
        shutil.copy(schema_path, os.path.join(STORE_AGENT_JSON_DIR, 'schema.json'))

        mpth_path = pkg_resources.resource_filename(__name__, 'data/default_multipath.conf')
        shutil.copy(mpth_path, os.path.join(STORE_AGENT_CONF_DIR, 'default_multipath.conf'))


COMMAND_CLASS = {
        'build_ext': BuildExt,
        'install_lib': post_install,
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
    os.path.join(os.path.dirname(__file__), 'storeagent', '__init__.py')
    ) as f:
    VERSION = re.match(r".*__version__ = '(.*?)'", f.read(), re.S).group(1)

with open(
    os.path.join(os.path.dirname(__file__), 'README.md')
    ) as f:
    DESCRIPION = f.read()

setup(
    name='storeagent',
    version=VERSION,
    description='storeagent  gRPC server for VIK',
    long_description=DESCRIPION,
    author='gaosong',
    author_email='gaosong@163.com',
    packages=find_packages(),
    data_files=[('data', ['data/storeagent.cfg', 'data/schema.json', 'data/default_multipath.conf'])],
    license=LICENSE,
    classifiers=CLASSIFIERS,
    install_requires=INSTALL_REQUIRES,
    python_requires='>=3',
    url='www.163.com',
    cmdclass=COMMAND_CLASS,
    entry_points={
        'console_scripts': [
            'storeagentd=storeagent.storeagentd:main',
            'store_agent_cli=storeagent.storeagentd:main_cli',
        ],
    }
)


