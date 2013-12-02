#!/usr/bin/env python
import unittest

from mock import patch, Mock
from StringIO import StringIO
from ConfigParser import NoOptionError
from boto import ec2

from simplesnapshot.snapshot import SimpleSnapshotConsole
from simplesnapshot.cmdline import *

class TestCmdline(unittest.TestCase):

    def setUp(self):

        self.fakeconn = Mock(spec=ec2.EC2Connection)
        self.fakecmdline = ("-c /etc/config -p testing -r us-east-1 -y "
                            "--dry-run list "
                            "--filter volume-id=vol-123456").split()
        self.fakeconfig = {
            "aws_access_key_id": "AMZTESTPASS",
            "aws_secret_access_key": "AMZESTKEY"
        }

        # Fake parse_config
        self.parse_args_patch = patch("simplesnapshot.cmdline.parse_args",
                                      autospec=True)
        self.mock_parse_args = self.parse_args_patch.start()

        # Fake read_config
        self.read_config_patch = patch("simplesnapshot.cmdline.read_config",
                                       autospec=True)
        self.mock_read_config = self.read_config_patch.start()
        self.mock_read_config.return_value = self.fakeconfig

        # Fake ec2 connection object
        self.ec2_patch = patch("simplesnapshot.cmdline.ec2")
        self.mock_ec2 = self.ec2_patch.start()
        self.mock_ec2.connect_to_region.return_value = self.fakeconn

        # Fake Snapshot
        self.snapshot_patch = patch(
            "simplesnapshot.cmdline.SimpleSnapshotConsole",
            autospec=True
        )
        self.mock_snapshot = self.snapshot_patch.start()
        self.mock_snapshot_instance = Mock(spec=SimpleSnapshotConsole)
        self.mock_snapshot_instance.run.side_effect = RuntimeError(
            "Testing SimpleSnapshotConsole call"
        )
        self.mock_snapshot.return_value = self.mock_snapshot_instance


    def tearDown(self):
        self.parse_args_patch.stop()
        self.read_config_patch.stop()
        self.ec2_patch.stop()
        self.snapshot_patch.stop()

    def test_list_parser(self):
        cmd_line = "list snap-123456 snap-54321"
        args = parse_args(cmd_line.split())
        self.assertEquals(args.command, "list")
        self.assertTrue(hasattr(args, 'profile'))
        self.assertTrue(hasattr(args, 'region'))
        self.assertTrue(hasattr(args, 'config'))
        self.assertTrue(hasattr(args, 'yes'))
        self.assertTrue(hasattr(args, 'dry_run'))
        self.assertTrue(hasattr(args, 'snapshot_ids'))
        self.assertTrue(hasattr(args, 'filters'))
        self.assertTrue(hasattr(args, 'count'))
        self.assertTrue(hasattr(args, 'limit'))
        self.assertTrue(hasattr(args, 'owner'))
        self.assertTrue(hasattr(args, 'type'))

    def test_delete_parser(self):
        cmd_line = "delete snap-123456 snap-54321"
        args = parse_args(cmd_line.split())
        self.assertEquals(args.command, "delete")
        self.assertTrue(hasattr(args, 'profile'))
        self.assertTrue(hasattr(args, 'region'))
        self.assertTrue(hasattr(args, 'config'))
        self.assertTrue(hasattr(args, 'yes'))
        self.assertTrue(hasattr(args, 'dry_run'))
        self.assertTrue(hasattr(args, 'snapshot_ids'))
        self.assertTrue(hasattr(args, 'filters'))
        self.assertTrue(hasattr(args, 'count'))
        self.assertTrue(hasattr(args, 'limit'))
        self.assertTrue(hasattr(args, 'type'))

    def test_create_parser(self):
        cmd_line = "create vol-123456"
        args = parse_args(cmd_line.split())
        self.assertEquals(args.command, "create")
        self.assertTrue(hasattr(args, 'profile'))
        self.assertTrue(hasattr(args, 'region'))
        self.assertTrue(hasattr(args, 'config'))
        self.assertTrue(hasattr(args, 'yes'))
        self.assertTrue(hasattr(args, 'dry_run'))
        self.assertTrue(hasattr(args, 'volume_id'))
        self.assertTrue(hasattr(args, 'description'))

    def test_config_missing_region(self):
        fp = StringIO()
        fp.write("[default]\n")
        fp.write("aws_access_key_id = AMZTESTPASS\n")
        fp.write("aws_secret_access_key = AMZTESTKEY\n")
        fp.seek(0)

        config = read_config(fp, "default")
        self.assertIsNone(config["region"])

    def test_config_missing_access_key(self):
        fp = StringIO()
        fp.write("[default]\n")
        fp.write("aws_secret_access_key = AMZTESTKEY\n")
        fp.write("region = us-west-2\n")
        fp.seek(0)

        self.assertRaises(NoOptionError, read_config, fp, "default")

    def test_config_missing_secret_key(self):
        fp = StringIO()
        fp.write("[default]\n")
        fp.write("aws_access_key_id = AMZTESTPASS\n")
        fp.write("region = us-west-2\n")
        fp.seek(0)

        self.assertRaises(NoOptionError, read_config, fp, "default")

    def test_parse_valid_items(self):
        fakeitems = ["Name=testCase", "Backup=Testing", "Group=WereTesting"]

        fakeitems_dict = {"Name": "testCase",
                          "Backup": "Testing",
                          "Group": "WereTesting"}

        parsed_items = parse_items(fakeitems)
        self.assertEquals(parsed_items, fakeitems_dict)

    def test_parse_invalid_items(self):
        self.assertRaises(ValueError, parse_items, ["Broken=Testcase=Blah"])

    def test_main_parse_args_call_signature(self):
        self.mock_parse_args.side_effect = RuntimeError("Test parse_args call")
        self.assertRaises(RuntimeError, main, self.fakecmdline)
        self.mock_parse_args.assert_called_once_with(self.fakecmdline)

    def test_main_read_config_call_signature(self):
        self.parse_args_patch.stop()
        self.mock_read_config.side_effect = RuntimeError(
            "Test read_config call"
        )
        self.assertRaises(RuntimeError, main, self.fakecmdline)
        self.mock_read_config.assert_called_once_with("/etc/config",
                                                      "testing")
        self.parse_args_patch.start()

    def test_main_ec2_call_signature(self):
        self.parse_args_patch.stop()
        self.mock_ec2.connect_to_region.side_effect = RuntimeError(
            "Test EC2 connect_to_region call"
        )
        self.assertRaises(RuntimeError, main, self.fakecmdline)
        self.mock_ec2.connect_to_region.assert_called_once_with(
            "us-east-1",
            aws_access_key_id=self.fakeconfig["aws_access_key_id"],
            aws_secret_access_key=self.fakeconfig["aws_secret_access_key"]
        )
        self.parse_args_patch.start()

    def test_main_list_call_signature(self):
        self.parse_args_patch.stop()
        self.assertRaises(RuntimeError, main, self.fakecmdline)
        self.mock_snapshot.assert_called_once_with(self.fakeconn,
                                                   snapshot_ids=[],
                                                   volume_id=None,
                                                   description="",
                                                   count=0,
                                                   limit=0,
                                                   count_type="num",
                                                   filters={
                                                       "volume-id": "vol-123456"
                                                   },
                                                   tags={},
                                                   owner="self",
                                                   auto_confirm=True,
                                                   dry_run=True)
        self.mock_snapshot_instance.run.assert_called_once_with("list")
        self.parse_args_patch.start()

    def test_main_create_call_signature(self):
        self.parse_args_patch.stop()
        cmdline = ("-y --region ap-northwest-1 create "
                   "--description CreateTest --tags Name=Test "
                   "Type=UnderTest -- vol-9999999").split()
        self.assertRaises(RuntimeError, main, cmdline)
        self.mock_snapshot.assert_called_once_with(self.fakeconn,
                                                   snapshot_ids=[],
                                                   volume_id="vol-9999999",
                                                   description="CreateTest",
                                                   count=0,
                                                   limit=0,
                                                   count_type="num",
                                                   filters={},
                                                   tags={"Name": "Test",
                                                         "Type": "UnderTest"},
                                                   owner="self",
                                                   auto_confirm=True,
                                                   dry_run=False)
        self.mock_snapshot_instance.run.assert_called_once_with("create")
        self.parse_args_patch.start()

    def test_main_delete_call_signature(self):
        self.parse_args_patch.stop()
        cmdline = ("-y --r eu-west-1 delete --count=2 --type=days "
                   "--filter Name=Backup -- snap-111111").split()
        self.assertRaises(RuntimeError, main, cmdline)
        self.mock_snapshot.assert_called_once_with(self.fakeconn,
                                                   snapshot_ids=["snap-111111"],
                                                   volume_id=None,
                                                   description="",
                                                   count=2,
                                                   limit=0,
                                                   count_type="days",
                                                   filters={"Name": "Backup"},
                                                   tags={},
                                                   owner="self",
                                                   auto_confirm=True,
                                                   dry_run=False)
        self.mock_snapshot_instance.run.assert_called_once_with("delete")
        self.parse_args_patch.start()
