#!/usr/bin/env python

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(
    name='sulu',
    version='0.1.20130404.2',
    description='Sign update.rdf of mozilla add-ons in Python',
    long_description=open('README.rst').read(),
    author='Hector Zhao',
    author_email='bzhao@mozilla.com',
    url='https://github.com/l-hedgehog/sulu',
    py_modules=['sulu'],
    requires=['lxml', 'M2Crypto', 'pyasn1', 'rdflib (==3.1.0)'],
    provides=['sulu'],
    install_requires=['lxml', 'M2Crypto', 'pyasn1', 'rdflib==3.1.0'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        ],
    license='MPL 2.0',
    entry_points={
        'console_scripts': [
            'sulu=sulu:main'
        ]
    }
)
