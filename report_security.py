#!/usr/bin/env python3
"""Summarise a set of network security rule yaml files"""
#
# An initial attempt at writing a tool to mine the dumpped data.
#

import argparse
import collections
import ctypes
import glob
import os
import socket
import yaml


# FFS, python, what happened to "batteries included"?
# https://bugs.python.org/issue24809
#
def getprotobynumber(proto):
    libc = ctypes.CDLL("libc.so.6")
    libc.getprotobynumber.restype = ctypes.POINTER(ctypes.c_char_p)
    res = libc.getprotobynumber(proto)
    return res.contents.value.decode("utf8")


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
        help="Which directory to scan for SGR items",
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
db["acl"] = {}
db["elb"] = {}
db["instance"] = {}
db["sg"] = {}
db["sg_instances"] = {}
db["sg_elb"] = {}
db["sgr"] = {}
db["vpc"] = {}


def acl_name(_id):
    if _id not in db["acl"]:
        return f"? ({_id})"

    name = "?"
    for tag in db["acl"][_id].get("Tags", []):
        if tag["Key"] != "Name":
            continue
        name = tag["Value"].lower()

    return f"{name} ({_id})"


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


def group_name(_id):
    if _id not in db["sg"]:
        return f"? ({_id})"

    name = "?"
    if "GroupName" in db["sg"][_id]:
        name = db["sg"][_id]["GroupName"].lower()

    return f"{name} ({_id})"


def vpc_name(_id):
    if _id not in db["vpc"]:
        return f"? ({_id})"

    name = "?"
    for tag in db["vpc"][_id].get("Tags", []):
        if tag["Key"] != "Name":
            continue
        name = tag["Value"].lower()

    return f"{name} ({_id})"


def data_add_acl(_id, item):
    db["acl"][_id] = item


def data_add_instance(_id, item):
    db["instance"][_id] = item
    for group in item.get("SecurityGroups", []):
        groupid = group["GroupId"]
        db["sg_instances"].setdefault(groupid, set()).add(_id)


def data_add_sg(_id, item):
    db["sg"][_id] = item


def data_add_sgr(_id, item):
    db["sgr"][_id] = item


def data_add_vpc(_id, item):
    db["vpc"][_id] = item


def data_add_elb(_id, item):
    db["elb"][_id] = item
    for groupid in item.get("SecurityGroups", []):
        db["sg_elb"].setdefault(groupid, set()).add(_id)


def dump_all_acl():
    acls = {}
    for _id, acl in db["acl"].items():
        name = acl_name(_id)
        acls[name] = acl

        rules = []
        for entry in acl["Entries"]:
            if "PortRange" in entry:
                _from = entry["PortRange"]["From"]
                _to = entry["PortRange"]["To"]
                if _from == _to:
                    entry["PortRange"] = _from
                else:
                    entry["PortRange"] = f"{_from}-{_to}"
            else:
                entry["PortRange"] = "*"

            proto = int(entry["Protocol"])
            if proto == -1:
                entry["Protocol"] = "*"
            else:
                entry["Protocol"] = getprotobynumber(proto)

            rule = {}
            rule["RuleNumber"] = entry["RuleNumber"]
            rule["Protocol"] = entry["Protocol"]
            rule["RuleAction"] = entry["RuleAction"]

            if entry["Egress"]:
                rule["SrcAddr"] = "*"
                rule["DstAddr"] = entry["CidrBlock"]
                rule["SrcPort"] = entry["PortRange"]
                rule["DstPort"] = "*"
                rule["_order"] = entry["RuleNumber"] + 0.1
            else:
                # "Inbound rules"
                rule["SrcAddr"] = entry["CidrBlock"]
                rule["DstAddr"] = "*"
                rule["SrcPort"] = "*"
                rule["DstPort"] = entry["PortRange"]
                rule["_order"] = entry["RuleNumber"] + 0.0

            rules.append(rule)

        acl["_rules"] = rules

    columns = [
        "RuleNumber",
        "SrcAddr",
        "DstAddr",
        "Protocol",
        "SrcPort",
        "DstPort",
        "RuleAction",
    ]

    for name, acl in sorted(acls.items()):
        vpc = acl.get("VpcId", "")
        if vpc:
            vpc = f"(Vpc: {vpc_name(vpc)})"
        print()
        print("Acl:", name, vpc)

        print(str_table(acl["_rules"], columns, orderby="_order"))


def dump_all_sg():
    groups = {}
    for rule in db["sgr"].values():
        group = groups.setdefault(rule["GroupId"], [])

        # Make the ports human readable
        _from = rule['FromPort']
        _to = rule['ToPort']
        if _from == _to:
            ports = _from
        else:
            ports = f"{_from}-{_to}"
        rule["PortRange"] = ports

        group.append(rule)

    group_names = {}
    for _id in groups.keys():
        name = group_name(_id)
        group_names[name] = _id

    for name, _id in sorted(group_names.items()):
        sg = db["sg"].get(_id, {})
        group = groups[_id]

        print()
        print("Group:", name)
        if "Description" in sg:
            print("Description:", sg["Description"])

        instances = set()
        if _id in db["sg_instances"]:
            for instance in db["sg_instances"][_id]:
                instances.add(instance_name(instance))

        elbs = set()
        if _id in db["sg_elb"]:
            for elb in db["sg_elb"][_id]:
                elbs.add(elb)

        for elb in sorted(elbs):
            print("ELB", elb)
        for instance in sorted(instances):
            print("Instance", instance)

        rules = []
        for entry in group:
            rule = {}
            rule["Protocol"] = entry["IpProtocol"]
            rule["RuleAction"] = "ALLOW"

            if rule["Protocol"] == "-1":
                rule["Protocol"] = "*"

            if entry["PortRange"] == -1:
                entry["PortRange"] = "*"

            if "Description" in entry:
                rule["Description"] = entry["Description"]

            if entry["Tags"]:
                rule["Tags"] = tags_to_sane(entry["Tags"])

            if "CidrIpv4" in entry:
                addr = entry["CidrIpv4"]

            if "ReferencedGroupInfo" in entry:
                addr = entry["ReferencedGroupInfo"]["GroupId"]

            if entry["IsEgress"]:
                rule["SrcAddr"] = "$this"
                rule["DstAddr"] = addr
                rule["SrcPort"] = entry["PortRange"]
                rule["DstPort"] = "*"
            else:
                # "Inbound rules"
                rule["SrcAddr"] = addr
                rule["DstAddr"] = "$this"
                rule["SrcPort"] = "*"
                rule["DstPort"] = entry["PortRange"]

            orderby = []
            orderby.append(port2sortable(rule["SrcPort"]))
            orderby.append(port2sortable(rule["DstPort"]))
            orderby.append(ipaddr2sortable(rule["SrcAddr"]))
            orderby.append(ipaddr2sortable(rule["DstAddr"]))
            rule["_order"] = ".".join(orderby)

            rules.append(rule)

        columns = [
            "RuleNumber",
            "SrcAddr",
            "DstAddr",
            "Protocol",
            "SrcPort",
            "DstPort",
            "RuleAction",
            "Description",
            "Tags",
        ]

        print(str_table(rules, columns, orderby="_order"))


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
            if raw["datatype"] == "aws.ec2.network_acls":
                data_add_acl(_id, item)
                continue
            if raw["datatype"] == "aws.ec2.security_group_rules":
                data_add_sgr(_id, item)
                continue
            if raw["datatype"] == "aws.ec2.security_groups":
                data_add_sg(_id, item)
                continue
            if raw["datatype"] == "aws.ec2.vpcs":
                data_add_vpc(_id, item)
                continue
            if raw["datatype"] == "aws.elbv2.load_balancers":
                data_add_elb(_id, item)
                continue


def main():
    args = argparser()

    load_data(args)

    dump_all_acl()
    dump_all_sg()


if __name__ == "__main__":
    main()
