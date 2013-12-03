# Copyright 2013 Nick Downs
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

import sys

from datetime import datetime, timedelta
from boto.exception import EC2ResponseError


class SnapshotWrapper(object):
    """Wrapper class for boto.ec2.snapshot.Snapshot

    This wrapper class exposes a datetime object to allow for easy
    date comparison.

    Instances of this object will pass all attribute calls down
    to the wrapped snapshot object. This allows for SnapshotWrapper
    instances to match the API of the boto Snapshot class.

    """

    def __init__(self, snapshot):
        self._snapshot = snapshot

        # This assumes Amazon timestamps are always UTC
        self.date = datetime.strptime(self._snapshot.start_time,
                                      "%Y-%m-%dT%H:%M:%S.%fZ")

    def __getattr__(self, attr):
        return self._snapshot.__getattribute__(attr)


class SimpleSnapshot(object):
    """Base class for sorted snapshot discovery.

    Snapshots will be discovered and sorted by date. By default,
    snapshots are retrieved for the API key owner only. The class
    constructor has parameters that allow for filtering snapshots
    during the discovery phase. See the constructor docstring for
    more information on filtering.

    Each snapshot found is wrapped in a SnapshotWrapper instance.
    This allows us to easily sort the snapshot sequence by
    date. Sorting is done newest to oldest.

    The `get_snapshots` method returns a list of snapshots after
    filtering of that list has been done. It can also return the
    sequence of snapshots in reverse order. Please see `get_snapshots`
    docstring for more information.

    """

    def __init__(self, ec2_conn, snapshot_ids=[], count=0, limit=0,
                 count_type='num', filters={}, owner=["self"],
                 from_date=datetime.utcnow()):
        """Initialize a SimpleSnapshot instance

        :type conn: class:`boto.ec2.EC2Connection`
        :param conn: An EC2Connection instance like that returned by
            `boto.ec2.connect_to_region`

        :type snapshot_ids: list
        :param snapshot_ids: A list of EBS snapshot ids

        :type count: int
        :param count: If `count_type` is set to 'num', the
            `get_snapshots` method will match `count` number of
            snapshots. If `count_type` is set to 'days', the
            `get_snapshots` method will return all snapshots that were
            taken between now and `count` days ago.

        :type limit: int
        :param limit: Limit the number of snapshots returned by
            `get_snapshots`.  For example, set `limit` to 2 in order
            to have `get_snapshots` return the 2 oldest snapshots.

        :type count_type: string
        :param count_type: Controls the filter function used when
            searching for snapshots.

            Valid values are 'num' or 'days'. Default is 'num'.

        :type filters: dict
        :param filters: A dictionary of filters used to filter
            snapshots. See the AWS documentation for supported
            filter keys and values.

            http://docs.aws.amazon.com/

        :type owner: list
        :param owner: Only snapshots owned by `owner` will be
           discovered. Valid values are: 'self', 'amazon' or an
           AWS Account ID.

           Default value is 'self'.

        :type from_date: class:`datetime.datetime`
        :param from_date: A datetime.datetime instance that is
            used for the base time of date based searches. This
            attribute is used for unit tests but may have other
            good uses.

        """

        self.conn = ec2_conn
        self.snapshot_ids = snapshot_ids
        self.count = count
        self.limit = limit
        self.count_type = count_type
        self.filters = filters
        self.owner = owner
        self.from_date = from_date

        # set the filter function
        if self.count_type == "days":
            self._filter_func = self._by_days
        elif self.count_type == 'num':
            self._filter_func = self._by_num
        else:
            raise ValueError("Invalid count_type: {0}".format(self.count_type))

        self._snapshots = None

    @property
    def snapshots(self, update=False):
        """A list of snapshots

        :type update: boolean
        :param update: If set to true, the list of raw snapshots
            will be requested directly from AWS. If set to False,
            a cached list of snapshots will be returned.

            Default value is False.

        :rtype: list
        :return: The non-filtered list of snapshots.

        """
        if update or self._snapshots is None:
            self._find_snapshots()

        return self._snapshots

    def _find_snapshots(self):
        snaps = self.conn.get_all_snapshots(self.snapshot_ids,
                                            owner=self.owner,
                                            filters=self.filters)

        # Wrap each snapshot and sort the list newest to oldest.
        wrapped = [SnapshotWrapper(x) for x in snaps]
        self._snapshots = sorted(wrapped, key=lambda snap: snap.date,
                                 reverse=True)

    def _by_days(self, inverse=False):
        max_date = self.from_date + timedelta(days=-self.count)
        for snap in self.snapshots:
            if self.count <= 0:
                # Negative count disables count so return all
                # snapshots.
                yield snap
            elif inverse:
                if snap.date < max_date:
                    yield snap
            elif snap.date >= max_date:
                yield snap

    def _by_num(self, inverse=False):
        # We do not want a list slice done with a negative
        # number. A negative count therefore disables count
        # altogether.
        count = self.count if self.count > 0 else None
        if inverse:
            # Return the slice that is outside of the matched set.
            return (x for x in self.snapshots[count:])
        else:
            return (x for x in self.snapshots[:count])

    def get_snapshots(self, inverse=False):
        """A generator method that yields snapshots after filtering

        :type inverse: boolean
        :param inverse: Yield snapshots from oldest to newest instead
            of the default newest to oldest.

        :rtype: generator
        :return: Yields individual snapshots after filtering. The
            number of snapshots yielded will be limited based on the
            value of `limit` passed to the constructor.

        """

        snapshots = list(self._filter_func(inverse=inverse))
        if inverse:
            snapshots.reverse()

        counter = 0
        for snap in snapshots:
            if self.limit > 0 and counter >= self.limit:
                break
            else:
                yield snap

            counter += 1

    def run(self):
        raise NotImplementedError("Must be defined in a subclass")


class SimpleSnapshotConsole(SimpleSnapshot):

    def __init__(self, *args, **kwargs):
        """A console based driver for SimpleSnapshot

        :type auto_confirm: boolean
        :param auto_confirm: Automatically answer yes to all questions
            that would otherwise prompt the end user for confirmation.

        :type description: string
        :param description: The description string for a created snapshot.

        :type tags: dict
        :param tags: A dictionary containing tags that will be created
            during the snapshot creation process. Each Key/Value pair
            is maped to an AWS Tag Name and Value.

        :type volume_id: string
        :param volume_id: A volume_id string used by the `create` command.

        :type dry_run: boolean
        :param dry_run: Enable dry_run mode for create and delete
            actions.

        """

        self.auto_confirm = kwargs.pop('auto_confirm', None)
        self.description = kwargs.pop('description', "")
        self.tags = kwargs.pop('tags', {})
        self.volume_id = kwargs.pop('volume_id', None)
        self.dry_run = kwargs.pop('dry_run', False)

        super(SimpleSnapshotConsole, self).__init__(*args, **kwargs)

    def list(self):
        """List Snapshots

        Gather a list of snapshots based on owner and filter information.
        The snapshots will be listed from the most recent start_time to the
        oldest start_time.

        """

        self.output_header()
        for snap in self.get_snapshots():
            self.output_snap(snap)

    def create(self):
        """Create a snapshot for `volume_id`

        Description and tags are also set based off the
        `description` and `tags` instance attributes.

        """

        prompt = "Create snapshot for {0}".format(self.volume_id)
        if self.auto_confirm or self.confirm(prompt):
            self.output_header()
            try:
                snap = self.conn.create_snapshot(self.volume_id,
                                                 description=self.description,
                                                 dry_run=self.dry_run)

                self.output_snap(snap)

                if self.tags:
                    self.conn.create_tags(snap.id, self.tags,
                                          dry_run=self.dry_run)

            except EC2ResponseError, e:
                self._handle_error(e)

    def delete(self):
        """Delete snapshots starting from the oldest

        Snapshots are always sorted by date. Deletion begins from the oldest
        snapshot and continues up until the newest snapshot. You can limit
        the number of deletions by using the `count` and `limit` attributes.

        """

        candidates = list(self.get_snapshots(inverse=True))
        self.output_header()
        for snap in candidates:
            self.output_snap(snap)

        if self.auto_confirm or self.confirm("Delete Snapshots?"):
            try:
                for snap in candidates:
                    snap.delete(dry_run=self.dry_run)

            except EC2ResponseError, e:
                self._handle_error(e)

    def run(self, command):
        """Execute the command method

        :type command: string
        :param command: The command name to be executed when the
            `run` method is called. Possible values are 'list',
            'create', and 'delete'.

        """

        return getattr(self, command)()

    def _handle_error(self, error):
        if error.error_code == "DryRunOperation":
            print("{0}: {1}".format(error.error_code, error.error_message))
        else:
            raise

    @staticmethod
    def output_snap(snap):
        """Prints a single Snapshot's Information"""

        print("{0.id:<14}{0.status:<10}{0.progress:<5}{0.start_time:<25}"
              "{0.region.name:<15}{0.volume_id:<13}"
              "{0.description}".format(snap))

    @staticmethod
    def output_header():
        """Prints a header for snapshot information"""
        colums = ["SNAPSHOT_ID", "STATUS", "%", "START_TIME", "REGION",
                  "VOLUME_ID", "DESCRIPTION"]
        print("{0:<14}{1:<10}{2:<5}{3:<25}{4:<15}{5:<13}"
              "{6}".format(*colums))

    @staticmethod
    def confirm(prompt):
        """Generic user confirmation method"""

        answer = ""
        while answer not in ['y', 'n', 'yes', 'no']:
            print("{0} [y/n]: ".format(prompt), end="", file=sys.stderr)
            answer = raw_input()

        return (answer in ['y', 'yes'])
