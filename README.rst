###################
ec2-simple-snapshot
###################
.. image:: https://travis-ci.org/nickryand/ec2-simple-snapshot.png?branch=master
   :target: https://travis-ci.org/nickryand/ec2-simple-snapshot
   :alt: Build Status

************
Introduction
************

ec2-simple-snapshot is a command line tool designed to make dealing
with EBS snapshots simple. This tool requires Python 2.7 and the
boto module.

************
Installation
************

Install via `pip`_::

   $ sudo pip install ec2-simple-snapshot

Install from source::

   $ git clone https://github.com/nickryand/ec2-simple-snapshot.git
   $ cd ec2-simple-snapshot
   $ sudo python setup.py install

*************
Configuration
*************

Authentication credentials are stored in a configuration file. Create
a configuration file like the following. Be sure to replace the example
credentials here with your own aws credentials::

    [default]
    aws_access_key_id = AKTESTACCESSID
    aws_secret_access_key = wJalrXUtnBERF\GF84d91!PxRfiCYEXAMPLEKEY
    region = us-west-2

The region directive is optional here. However, if it is not set, you
must set the region using the ``-r REGION`` or ``--region REGION``
command line option.

Default location: ``~/.aws/config``

If you would like to have your configuration file elsewhere, use the
``-c <path to config>`` or ``--config <path to config>`` command line
option to tell ec2-simple-snapshot where to look.

Default Profile: ``default``

Very similar to the aws-cli tool from Amazon, you can store multiple
profiles in a single configuration file. This allows you to set multiple
sets of credentials using profiles to separate them. The default profile
is named ``default`` but can be changed using the ``-p PROFILE`` or
``--profile PROFILE`` command line option.

Example::

    [production]
    aws_access_key_id = AKTESTACCESSID
    aws_secret_access_key = wJalrXUtnBERF\GF84d91!PxRfiCYEXAMPLEKEY
    region = us-east-1

******************
IAM Policy Actions
******************

This is a list of the required set of IAM actions needed for each command.

* List

  - ec2:DescribeSnapshots

* Create

  - ec2:DescribeVolumes
  - ec2:CreateSnapshot
  - ec2:CreateTags

* Delete

  - ec2:DescribeSnapshots
  - ec2:DeleteSnapshot

**************
Usage Examples
**************
Show help screen::

    $ ec2-simple-snapshot -h

Show help screen for a subcommand::

    $ ec2-simple-snapshot <command> -h

List the two newest snapshots owned by your AWS Account::

    $ ec2-simple-snapshot list --count 2

List snapshots taken within the last 4 days::

    $ ec2-simple-snapshot list --count 4 --type days

Delete snapshots older than 3 days that have the tag "Type=Backup" and "Name=Test"::

    $ ec2-simple-snapshot delete --count 3 --type days --filter 'Type=Backup' 'Name=Test'

Delete all but the last 30 snapshots, however limit deletes to 2::

    $ ec2-simple-snapshot delete --count 30 --limit 2

Create a snapshot for volume 'vol-123456' setting a description and adding a tag::

    $ ec2-simple-snapshot create \
    > --description "This is a test"
    > --tags "Environment=Production" vol-123456

**********
Test Suite
**********

The easiest way to get started with the testing suite is to use the `tox`_
automation project.

Install tox::

    $ pip install tox

Run the test suite::

    $ git clone https://github.com/nickryand/ec2-simple-snapshot.git
    $ cd ec2-simple-snapshot
    $ tox

If you do not want to use tox, you can install the development dependencies
using `pip`_ and use the python unittest module to execute the tests.

Install dependencies and run suite::

    $ git clone https://github.com/nickryand/ec2-simple-snapshot.git
    $ cd ec2-simple-snapshot
    $ pip install -r requirements.txt
    $ python -m unittest discover

.. _pip: http://www.pip-installer.org/
.. _tox: http://tox.readthedocs.org/en/latest/
