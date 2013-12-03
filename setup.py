#!/usr/bin/env python
from setuptools import setup

from simplesnapshot import __version__

setup(
    name="ec2-simple-snapshot",
    version=__version__,
    description="A tool to make EC2 snapshot manipulation easier.",
    long_description=file("README.rst").read(),
    packages=["simplesnapshot"],
    entry_points={
        "console_scripts": [
            'ec2-simple-snapshot = simplesnapshot:main',
        ]
    },
    author="Nick Downs",
    author_email="nickryand@gmail.com",
    license="Apache 2.0",
    platforms="Posix; MacOS X",
    url="http://github.com/nickryand/ec2-simple-snapshot",
    install_requires=["boto == 2.16.0"],
    classifiers=(
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Natural Language :: English',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7'
    )
)
