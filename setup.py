
import sys

from setuptools import setup
from setuptools.command.test import test as TestCommand

import ipcqueue


class PyTest(TestCommand):

    user_options = [
        ('pytest-args=', 'a', "Arguments to pass to py.test"),
    ]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = []

    def run_tests(self):
        import pytest
        errno = pytest.main(self.pytest_args)
        sys.exit(errno)


description = (
    "Ipcqueue provides POSIX and SYS V message queues functionality to "
    "exchange data among processes."
)

try:
    if sys.version_info >= (3,):
        long_description = open('README.rst', 'rb').read().decode('utf-8')
    else:
        long_description = open('README.rst', 'r').read().decode('utf-8')
except IOError:
        long_description = description

setup(
    name="ipcqueue",
    version=ipcqueue.__version__,
    author='Jan Seifert',
    author_email="jan.seifert@fotkyzcest.net",
    description=description,
    long_description=long_description,
    keywords="sysv posix ipc queue",
    url='https://github.com/seifert/ipcqueue',
    license="BSD",
    classifiers=[
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'License :: OSI Approved :: BSD License',
        'Operating System :: POSIX',
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    packages=['ipcqueue'],
    zip_safe=False,
    setup_requires=[
        'cffi>=1',
    ],
    install_requires=[
        'cffi>=1',
    ],
    tests_require=[
        'pytest>=3',
    ],
    test_suite='tests',
    cmdclass={
        'test': PyTest,
    },
    cffi_modules=[
        'cffi_builder_posix.py:ffibuilder',
        'cffi_builder_sysv.py:ffibuilder',
    ],
)
