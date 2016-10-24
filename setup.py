#!/usr/bin/env python
from setuptools import setup

setup(
    name='puzpy',
    version='0.2.3',
    description='python crossword puzzle library',
    author='Alex Dejarnatt',
    author_email='adejarnatt@gmail.com',
    maintainer='Simeon Visser',
    maintainer_email='simeonvisser@gmail.com',
    url='https://github.com/alexdej/puzpy',
    download_url='https://pypi.python.org/pypi/puzpy',
    py_modules=['puz'],
    install_requires=[],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Topic :: Games/Entertainment :: Puzzle Games',
    ],
    keywords='puz crosswords crossword puzzle acrosslite xword xwords'
)
