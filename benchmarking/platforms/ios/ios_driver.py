#!/usr/bin/env python

##############################################################################
# Copyright 2017-present, Facebook, Inc.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.
##############################################################################

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
import json
import re
from six import string_types

from platforms.ios.idb import IDB
from platforms.ios.ios_platform import IOSPlatform


class IOSDriver(object):
    def __init__(self, args, devices=None):
        self.args = args
        self.devices = self.getDevices()
        if devices:
            if isinstance(devices, string_types):
                devices = [devices]
            self.devices = {d: self.devices[d] for d in self.devices if d in devices}
        self.type = "ios"

    def getDevices(self, silent=False):
        idb = IDB()
        rows = idb.run(["--detect", "--timeout", "1"], silent=silent)
        if len(rows) == 0:
            return {}
        rows.pop(0)
        pattern = re.compile(r".* Found ([\d|a-f|\-|A-F]+) \((\w+), .+, .+, (.+), (.+), .+\) a\.k\.a\. .*")
        devices = {}
        for row in rows:
            match = pattern.match(row)
            if match:
                hash = match.group(1)
                model = match.group(2)
                abi = match.group(3)
                os_version = match.group(4)
                devices[hash] = {"model":model, "abi":abi, "os_version":os_version}
        return devices

    def getIOSPlatforms(self, tempdir):
        platforms = []
        if self.args.device:
            device_str = self.args.device
            assert device_str[0] == '{', "device must be a json string"
            device = json.loads(device_str)
            idb = IDB(device["hash"], tempdir)
            platform = IOSPlatform(tempdir, idb, self.args)
            platform.setPlatform(device["kind"])
            platform.setOSVersion(device.get("os_version", None))
            platform.setABI(device.get("abi", None))
            platforms.append(platform)
            return platforms

        if self.args.excluded_devices:
            excluded_devices = \
                set(self.args.excluded_devices.strip().split(','))
            self.devices = self.devices.difference(excluded_devices)

        if self.args.devices:
            supported_devices = set(self.args.devices.strip().split(','))
            if supported_devices.issubset(self.devices):
                self.devices = supported_devices

        for device in self.devices:
            idb = IDB(device, tempdir)
            platform_meta = {
                "os_version": self.devices[device]["os_version"],
                "model": self.devices[device]["model"],
                "abi": self.devices[device]["abi"]
            }
            platform = IOSPlatform(tempdir, idb, self.args, platform_meta)
            platform.setPlatform(device)
            platforms.append(platform)

        return platforms
