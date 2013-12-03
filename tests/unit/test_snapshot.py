#!/usr/bin/env python
import unittest

from datetime import datetime
from mock import patch, Mock
from boto.ec2 import EC2Connection
from boto.ec2.snapshot import Snapshot

from simplesnapshot.snapshot import *


class TestSimpleSnapshot(unittest.TestCase):

    def setUp(self):
        self.fake1 = Snapshot()
        self.fake1.start_time = "2013-09-21T02:05:32.000Z"
        self.fake1.id = "snap-1"
        self.fake2 = Snapshot()
        self.fake2.start_time = "2013-09-22T04:10:05.000Z"
        self.fake2.id = "snap-2"
        self.fake3 = Snapshot()
        self.fake3.start_time = "2013-09-22T22:09:57.000Z"
        self.fake3.id = "snap-3"
        self.fake4 = Snapshot()
        self.fake4.start_time = "2013-09-23T22:09:55.000Z"
        self.fake4.id = "snap-4"
        self.fake5 = Snapshot()
        self.fake5.start_time = "2013-09-24T22:09:55.000Z"
        self.fake5.id = "snap-5"

        # Semi random snapshot list.
        self.unsorted_snaps = [self.fake4, self.fake1, self.fake3,
                               self.fake5, self.fake2]

        self.fakedate = datetime(2013, 9, 25, 9, 56)
        self.fakeconn = Mock(spec=EC2Connection)
        self.fakeconn.get_all_snapshots.return_value = self.unsorted_snaps

    def test_correct_filter_select(self):
        snapshot = SimpleSnapshot(self.fakeconn, count_type="days")
        self.assertEqual(snapshot._filter_func, snapshot._by_days)

    def test_wrapped_snapshots(self):
        snapshot = SimpleSnapshot(self.fakeconn)
        for snap in snapshot.snapshots:
            self.assertIsInstance(snap, SnapshotWrapper)

    def test_proper_sort(self):
        snapshot = SimpleSnapshot(self.fakeconn)

        # The real snapshot object is available via the _snapshot private
        # attribute from the SnapshotWrapper class.
        self.assertEqual([x._snapshot for x in snapshot.snapshots],
                         [self.fake5, self.fake4, self.fake3,
                          self.fake2, self.fake1])

    def test_by_num(self):
        snapcount1 = SimpleSnapshot(self.fakeconn, count=1)
        self.assertEqual([x._snapshot for x in snapcount1.get_snapshots()],
                         [self.fake5])

        snapcount2 = SimpleSnapshot(self.fakeconn, count=2)
        self.assertEqual([x._snapshot for x in snapcount2.get_snapshots()],
                         [self.fake5, self.fake4])

        snapcount3 = SimpleSnapshot(self.fakeconn)
        self.assertEqual([x._snapshot for x in snapcount3.get_snapshots()],
                         [self.fake5, self.fake4, self.fake3,
                          self.fake2, self.fake1])

        snapnegative1 = SimpleSnapshot(self.fakeconn, count=-2)
        self.assertEqual([x._snapshot for x in snapnegative1.get_snapshots()],
                         [self.fake5, self.fake4, self.fake3,
                          self.fake2, self.fake1])

    def test_by_num_limit(self):
        snaplimit2 = SimpleSnapshot(self.fakeconn, limit=2)
        self.assertEqual([x._snapshot for x in snaplimit2.get_snapshots()],
                         [self.fake5, self.fake4])

        snaplimit4 = SimpleSnapshot(self.fakeconn, limit=4)
        self.assertEqual([x._snapshot for x in snaplimit4.get_snapshots()],
                         [self.fake5, self.fake4, self.fake3, self.fake2])

        snapnegative1 = SimpleSnapshot(self.fakeconn, limit=-1)
        self.assertEqual([x._snapshot for x in snapnegative1.get_snapshots()],
                         [self.fake5, self.fake4, self.fake3,
                          self.fake2, self.fake1])

    def test_by_num_inverse(self):
        snapinverse = SimpleSnapshot(self.fakeconn)
        self.assertEqual([x._snapshot for x in
                          snapinverse.get_snapshots(inverse=True)],
                         [self.fake1, self.fake2, self.fake3,
                          self.fake4, self.fake5])

        snapinverse1 = SimpleSnapshot(self.fakeconn, count=1)
        self.assertEqual([x._snapshot for x in
                          snapinverse1.get_snapshots(inverse=True)],
                         [self.fake1, self.fake2, self.fake3, self.fake4])

        snapinverse4 = SimpleSnapshot(self.fakeconn, count=4)
        self.assertEqual([x._snapshot for x in
                          snapinverse4.get_snapshots(inverse=True)],
                         [self.fake1])

        snapnegative = SimpleSnapshot(self.fakeconn, count=-2)
        self.assertEqual([x._snapshot for x in
                          snapnegative.get_snapshots(inverse=True)],
                         [self.fake1, self.fake2, self.fake3,
                          self.fake4, self.fake5])

    def test_inverse_limit(self):
        snapnum1 = SimpleSnapshot(self.fakeconn, limit=1)
        self.assertEqual([x._snapshot for x in
                          snapnum1.get_snapshots(inverse=True)],
                         [self.fake1])

        snapnum2 = SimpleSnapshot(self.fakeconn, count=2, limit=4)
        self.assertEqual([x._snapshot for x in
                          snapnum2.get_snapshots(inverse=True)],
                         [self.fake1, self.fake2, self.fake3])

        snapdays1 = SimpleSnapshot(self.fakeconn, count=2, limit=2,
                                   count_type="days")
        self.assertEqual([x._snapshot for x in
                          snapdays1.get_snapshots(inverse=True)],
                         [self.fake1, self.fake2])

        snapdays2 = SimpleSnapshot(self.fakeconn, count=1, limit=4,
                                   count_type="days")
        self.assertEqual([x._snapshot for x in
                          snapdays2.get_snapshots(inverse=True)],
                         [self.fake1, self.fake2, self.fake3, self.fake4])

        snapnegative1 = SimpleSnapshot(self.fakeconn, count=3, limit=-1)
        self.assertEqual([x._snapshot for x in
                          snapnegative1.get_snapshots(inverse=True)],
                         [self.fake1, self.fake2])

        snapnegative2 = SimpleSnapshot(self.fakeconn, count=-1,
                                       limit=-1, count_type="days")
        self.assertEqual([x._snapshot for x in
                          snapnegative2.get_snapshots(inverse=True)],
                         [self.fake1, self.fake2, self.fake3,
                          self.fake4, self.fake5])

        snapnegative3 = SimpleSnapshot(self.fakeconn, count=-1, limit=2)
        self.assertEqual([x._snapshot for x in
                          snapnegative3.get_snapshots(inverse=True)],
                         [self.fake1, self.fake2])

        snapnegative4 = SimpleSnapshot(self.fakeconn, count=-1, limit=4,
                                       count_type="days")
        self.assertEqual([x._snapshot for x in
                          snapnegative4.get_snapshots(inverse=True)],
                         [self.fake1, self.fake2, self.fake3, self.fake4])

    def test_by_days(self):
        snapshot1 = SimpleSnapshot(self.fakeconn, count=1,
                                   count_type="days", from_date=self.fakedate)
        self.assertEqual([x._snapshot for x in snapshot1.get_snapshots()],
                         [self.fake5])

        snapshot2 = SimpleSnapshot(self.fakeconn, count=3,
                                   count_type="days", from_date=self.fakedate)
        self.assertEqual([x._snapshot for x in snapshot2.get_snapshots()],
                         [self.fake5, self.fake4, self.fake3])

        snapshot3 = SimpleSnapshot(self.fakeconn, count=4,
                                   count_type="days", from_date=self.fakedate)
        self.assertEqual([x._snapshot for x in snapshot3.get_snapshots()],
                         [self.fake5, self.fake4, self.fake3, self.fake2])

        snapshot4 = SimpleSnapshot(self.fakeconn, count=3,
                                   count_type="days",
                                   from_date=datetime(2013, 9, 25))
        self.assertEqual([x._snapshot for x in snapshot4.get_snapshots()],
                         [self.fake5, self.fake4, self.fake3, self.fake2])

        snapnegative1 = SimpleSnapshot(self.fakeconn, count=-1,
                                       count_type="days",
                                       from_date=self.fakedate)
        self.assertEqual([x._snapshot for x in snapnegative1.get_snapshots()],
                         [self.fake5, self.fake4, self.fake3,
                          self.fake2, self.fake1])

    def test_by_days_inverse(self):
        snapshot1 = SimpleSnapshot(self.fakeconn, count=2,
                                   limit=1, count_type="days",
                                   from_date=self.fakedate)
        self.assertEqual([x._snapshot for x in
                          snapshot1.get_snapshots(inverse=True)],
                         [self.fake1])

        snapshot2 = SimpleSnapshot(self.fakeconn, count=3,
                                   count_type="days",
                                   from_date=self.fakedate)
        self.assertEqual([x._snapshot for x in
                          snapshot2.get_snapshots(inverse=True)],
                         [self.fake1, self.fake2])

        snapnegative1 = SimpleSnapshot(self.fakeconn, limit=-2,
                                       count_type="days",
                                       from_date=self.fakedate)
        self.assertEqual([x._snapshot for x in
                          snapnegative1.get_snapshots(inverse=True)],
                         [self.fake1, self.fake2, self.fake3,
                          self.fake4, self.fake5])

        snapnegative2 = SimpleSnapshot(self.fakeconn, count=-1,
                                       limit=4, count_type="days",
                                       from_date=self.fakedate)
        self.assertEqual([x._snapshot for x in
                          snapnegative2.get_snapshots(inverse=True)],
                         [self.fake1, self.fake2, self.fake3, self.fake4])


class TestSnapshotActions(unittest.TestCase):

    def setUp(self):
        self.fakesnap = Mock(spec=Snapshot)
        self.fakesnap.start_time = "2013-09-21T02:05:32.000Z"
        self.fakesnap.status = "completed"
        self.fakesnap.progress = "100%"
        self.fakesnap.region = Mock()
        self.fakesnap.region.name = "us-west-2"
        self.fakesnap.volume_id = "vol-1234567"
        self.fakesnap.id = "snap-1"
        self.fakesnap.description = "Snapshot Under test"
        self.fakesnap.delete = Mock()

        self.fakedate = datetime(2013, 9, 22)
        self.fakeconn = Mock(spec=EC2Connection)
        self.fakeconn.get_all_snapshots.return_value = [self.fakesnap]
        self.fakeconn.create_snapshot.return_value = self.fakesnap

    def test_create_snapshot(self):
        tags = {"Name": "Testing"}
        snap1 = SimpleSnapshotConsole(self.fakeconn,
                                      volume_id="vol-123456",
                                      tags=tags,
                                      auto_confirm=True)
        snap1.run("create")
        self.fakeconn.create_snapshot.assert_called_once_with("vol-123456",
                                                              description="",
                                                              dry_run=False)
        self.fakeconn.create_tags.assert_called_once_with(self.fakesnap.id,
                                                          tags,
                                                          dry_run=False)

    def test_create_snapshot_dry_run(self):
        snap = SimpleSnapshotConsole(self.fakeconn,
                                     volume_id="vol-3231412",
                                     auto_confirm=True, dry_run=True)
        snap.run("create")
        self.fakeconn.create_snapshot.assert_called_once_with("vol-3231412",
                                                              description="",
                                                              dry_run=True)

    def test_delete_snapshot(self):
        snap = SimpleSnapshotConsole(self.fakeconn, auto_confirm=True)
        snap.run("delete")
        self.fakesnap.delete.assert_called_once_with(dry_run=False)

    def test_delete_snapshot_dry_run(self):
        snap = SimpleSnapshotConsole(self.fakeconn, auto_confirm=True,
                                     dry_run=True)
        snap.run("delete")
        self.fakesnap.delete.assert_called_once_with(dry_run=True)
