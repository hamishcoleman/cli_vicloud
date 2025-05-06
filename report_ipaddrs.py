#!/usr/bin/env python3
"""Summarise all the ip addresses"""
#
#

import argparse
import collections
import glob
import os
import socket
import yaml


def port2sortable(s):
    """Convert a possible port string to a sortable string"""
    try:
        port = int(s)
    except ValueError:
        port = 0
    return f"{port:06}"


def ipaddr2sortable(s):
    """Convert a possible ipv4addr+subnet to a sortable string"""
    parts = s.split("/")

    # TODO: ipv6

    try:
        addr = socket.inet_aton(parts[0]).hex()
    except (OSError, NameError):
        addr = "00000000"

    if len(parts) > 1:
        addr += "/"
        addr += port2sortable(parts[1])

    return addr


def argparser():
    args = argparse.ArgumentParser(
        description=__doc__,
    )

    args.add_argument(
        "--profile",
        action="append",
        default=[],
        help="Select which awscli profile filter for",
    )
    args.add_argument(
        "--region",
        action="append",
        default=[],
        help="Select which aws region to filter for",
    )

    args.add_argument(
        "dirname",
        help="Which directory to scan for data files",
    )

    r = args.parse_args()
    return r


def str_table(rows, columns, orderby=None):
    """Given an array of dicts, do a simple table print"""
    result = list()
    widths = collections.defaultdict(lambda: 0)

    if len(rows) == 0:
        # No data to show, be sure not to truncate the column headings
        for col in columns:
            widths[col] = len(col)
    else:
        for row in rows:
            for col in columns:
                if col in row:
                    widths[col] = max(widths[col], len(str(row[col])))

    for col in columns:
        if widths[col] == 0:
            widths[col] = 1
        result += "{:{}.{}} ".format(col, widths[col], widths[col])
    result += "\n"

    if orderby is not None:
        rows = sorted(rows, key=lambda row: row.get(orderby, ""))

    for row in rows:
        for col in columns:
            if col in row:
                data = row[col]
            else:
                data = ''
            if isinstance(data, (list, dict)):
                data = str(data)

            result += "{:{}} ".format(data, widths[col])
        result += "\n"

    return ''.join(result)


def str_table_columns(rows):
    """Given an array of dicts, return a set of all column names"""

    columns = set()
    for row in rows:
        columns.update(row)

    return columns


db = {}
db["instance"] = {}
db["network_interface"] = {}
db["subnet"] = {}


def tags_to_sane(data):
    tags = {}
    for tag in data:
        if tag["Key"] in tags:
            raise ValueError("Duplicate tag name")
        tags[tag["Key"]] = tag["Value"]

    stags = {}
    for k, v in sorted(tags.items()):
        stags[k] = v
    return stags


def instance_name(_id):
    if _id not in db["instance"]:
        return f"? ({_id})"

    name = "?"
    for tag in db["instance"][_id].get("Tags", []):
        if tag["Key"] != "Name":
            continue
        name = tag["Value"].lower()

    return f"{name} ({_id})"


def data_add_instance(_id, item):
    db["instance"][_id] = item


def data_add_network_interface(_id, item):
    db["network_interface"][_id] = item


def data_add_subnet(_id, item):
    db["subnet"][_id] = item


def dump_all_ipaddrs():
    rows = []

    for _id, iface in db["network_interface"].items():
        meta = {}
        if "Attachment" in iface and "InstanceId" in iface["Attachment"]:
            meta["Description"] = instance_name(
                iface["Attachment"]["InstanceId"]
            )

        if "Tags" in iface:
            meta["Tags"] = tags_to_sane(iface["Tags"])

        if "Description" not in meta:
            meta["Description"] = iface["Description"]

        meta["SubnetId"] = iface["SubnetId"]
        meta["VpcId"] = iface["VpcId"]

        if "Association" in iface and "PublicIp" in iface["Association"]:
            this = meta.copy()
            this["IPv4"] = iface["Association"]["PublicIp"]
            this["_order"] = ipaddr2sortable(this["IPv4"])
            rows.append(this)

        this = meta.copy()
        this["IPv4"] = iface["PrivateIpAddress"]
        this["_order"] = ipaddr2sortable(this["IPv4"])
        rows.append(this)

    for _id, subnet in db["subnet"].items():
        this = {}
        this["IPv4"] = subnet["CidrBlock"]
        this["SubnetId"] = subnet["SubnetId"]
        this["VpcId"] = subnet["VpcId"]
        this["AvailableIpAddressCount"] = subnet["AvailableIpAddressCount"]

        if "Tags" in subnet:
            this["Tags"] = tags_to_sane(subnet["Tags"])

        if "Tags" in this and "Name" in this["Tags"]:
            this["Description"] = this["Tags"]["Name"]

        this["_order"] = ipaddr2sortable(this["IPv4"])
        rows.append(this)

    columns = [
        "IPv4",
        "Description",
        "SubnetId",
        "VpcId",
        "Tags",
    ]

    print(str_table(rows, columns, orderby="_order"))


def load_data(args):
    os.chdir(args.dirname)
    for filename in glob.glob("**/*.yaml", recursive=True):
        with open(filename, "r+") as f:
            raw = yaml.safe_load(f)
            if args.profile and raw["metadata"]["profile"] not in args.profile:
                continue
            if args.region and raw["metadata"]["region"] not in args.region:
                continue

            _id = raw["metadata"]["resourceid"]
            item = raw["specifics"]

            if raw["datatype"] == "aws.ec2.instances":
                data_add_instance(_id, item)
                continue
            if raw["datatype"] == "aws.ec2.network_interfaces":
                data_add_network_interface(_id, item)
                continue
            if raw["datatype"] == "aws.ec2.subnets":
                data_add_subnet(_id, item)
                continue


def main():
    args = argparser()

    load_data(args)

    dump_all_ipaddrs()


if __name__ == "__main__":
    main()
