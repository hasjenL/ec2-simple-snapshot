#!/usr/bin/env python
# Copyright (c) 2013 Nick Downs
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from __future__ import print_function
import os
import sys

from ConfigParser import SafeConfigParser, NoOptionError
from argparse import ArgumentParser

from boto import ec2
from simplesnapshot.snapshot import SimpleSnapshotConsole


def parse_args(args):
    """Parse arguments from string

    :type args: list
    :param args: A list of arguments to be parsed. An example of this
        type of list is sys.argv[1:].

    :rtype: class`argparse.Namespace`
    :return: An `argparse.Namespace` instance returned from parsing
        arguments with the argparse module.

    """

    parser = ArgumentParser()
    parser.add_argument("-p", "--profile", default="default",
                        help="Profile in aws config to use.")
    parser.add_argument("-r", "--region", default=None,
                        help="EC2 region to connect to.")
    parser.add_argument("-c", "--config", default="~/.aws/config",
                        help=("AWS cli configuration file location. "
                              "Default: %(default)s"))
    parser.add_argument("-y", "--yes", default=False, action="store_true",
                        help="Answer yes to all prompts automatically.")
    parser.add_argument("--dry-run", dest="dry_run", action="store_true",
                        default=False, help="Enable aws dry run mode.")

    # Sub parser for each supported command
    subparser = parser.add_subparsers(title="snapshot commands",
                                      dest="command")

    create_parser = subparser.add_parser("create", help="Create a snapshot")
    list_parser = subparser.add_parser("list", help="List snapshots")
    delete_parser = subparser.add_parser("delete", help="Delete Snapshots")

    for _parser in [list_parser, delete_parser]:
        _parser.add_argument("snapshot_ids", nargs="*", metavar="snapshot_id",
                             help="EC2 Snapshot identification numbers")
        _parser.add_argument("--filter", nargs="+", dest="filters",
                             metavar="\"name=value\"", default=[],
                             help=("Snapshot Filters. This option may "
                                   "be used multiple times. "
                                   "EXAMPLE: 'volume-id=vol-123456'"))
        _parser.add_argument("--count", default=0, type=int,
                             help="number of snapshots to operate on.")
        _parser.add_argument("--limit", default=0, type=int,
                             help="max number of snapshots to operate on.")
        _parser.add_argument("--type", default="num",
                             choices=["num", "days"],
                             help=("The type of filter you want to use."
                                   " 'num' will trigger a normal numerical"
                                   " filter. 'days' will filter by date."
                                   " DEFAULT: '%(default)s'"))

    list_parser.add_argument("--owner", default=["self"], nargs="+",
                             help=("Snapshot owner(s). Valid values are "
                                   "'self', 'amazon' and/or valid "
                                   "aws account ids. "
                                   "DEFAULT: 'self'"))

    create_parser.add_argument("volume_id",
                               help="EC2 EBS Volume Identification Number.")
    create_parser.add_argument("--description", default="",
                               help="Add a description to new snapshot.")
    create_parser.add_argument("--tags", nargs="+", dest="tags",
                               metavar="\"name=value\"", default=[],
                               help=("Tags to set on the Snapshot. This option"
                                     " may be used multiple times. "
                                     "EXAMPLE: 'type=backup'"))

    return parser.parse_args(args)


def read_config(fp, section):
    """Read a config file and ensure required sections exist

    :type fp: string or file-like object
    :param fp: The path to a configuration file or a file like object
        containing the configuration data.

    :type section: string
    :param section: The section of the configuration file to parse.
        The configuration file should be in the format parsable by the
        ConfigParser module.

    :rtype: dict
    :return: A dictionary containing the configuration file data.

    """
    if isinstance(fp, str):
        fp = file(os.path.expanduser(fp))

    conf = SafeConfigParser()
    conf.readfp(fp)

    items = {}
    items["aws_access_key_id"] = conf.get(section, 'aws_access_key_id')
    items["aws_secret_access_key"] = conf.get(section, 'aws_secret_access_key')
    try:
        items["region"] = conf.get(section, 'region')
    except NoOptionError, e:
        items["region"] = None

    return items


def parse_items(items):
    """Parse name=value strings into a dictionary

    :type items: iterable
    :param items: An interable of strings that match the syntax "name=value".

    :rtype: dict
    :return: A dictionary of key/value pairs created from the iterable of
        "name=value" strings.

    """

    items_dict = {}
    for arg in items:
        try:
            key, value = arg.split("=")
            if key:
                items_dict[key] = value
        except Exception, e:
            raise ValueError("Error parsing item {0}: {1}".format(arg, e))

    return items_dict


def main(argv):
    args = parse_args(argv)

    config = read_config(args.config, args.profile)

    # Update region from the command line if passed
    if args.region is not None:
        config['region'] = args.region

    conn = ec2.connect_to_region(
        config['region'],
        aws_access_key_id=config['aws_access_key_id'],
        aws_secret_access_key=config['aws_secret_access_key']
    )

    # Extensive use of getattr here so we can provide defaults and not
    # raise an exception for a missing attribute. This is done because
    # not all commands share the same command line arguments. For instance
    # the 'create' command does not support an 'owner' argument. Attempting
    # to access args.owner during a create snapshot run would raise an
    # AttributeError.
    command = SimpleSnapshotConsole(
        conn,
        snapshot_ids=getattr(args, "snapshot_ids", []),
        volume_id=getattr(args, "volume_id", None),
        description=getattr(args, "description", ""),
        count=getattr(args, "count", 0),
        limit=getattr(args, "limit", 0),
        count_type=getattr(args, "type", "num"),
        filters=parse_items(getattr(args,
                                    "filters", [])),
        tags=parse_items(getattr(args, "tags", [])),
        owner=' '.join(getattr(args, "owner", ["self"])),
        auto_confirm=args.yes,
        dry_run=args.dry_run
    )
    return command.run(args.command)

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
