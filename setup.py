#!/usr/bin/env python

from distutils.core import setup

setup(name='sulu',
      version='0.1.20120229.1',
      description='Sign update.rdf of mozilla add-ons in Python',
      author='Hector Zhao',
      author_email='bzhao@mozilla.com',
      url='https://github.com/l-hedgehog/sulu',
      py_modules=['sulu'],
      requires=['lxml', 'M2Crypto', 'pyasn1', 'rdflib'],
      provides=['sulu'],
      classifiers=[
          'Development Status :: 4 - Beta',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)',
          'Programming Language :: Python',
          ]
     )
