
import sys

from setuptools import setup, Extension

import ipcqueue


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
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'License :: OSI Approved :: BSD License',
        'Operating System :: POSIX',
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    packages=['ipcqueue'],
    ext_modules=[
        Extension(
            name='ipcqueue._posixmq',
            sources=['ipcqueue/_posixmq.c'],
            libraries=['rt'],
        ),
        Extension(
            name='ipcqueue._sysvmq',
            sources=['ipcqueue/_sysvmq.c'],
        ),
    ],
)
