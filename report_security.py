#!/usr/bin/env python3
"""Summarise a set of network security rule yaml files"""
#
# An initial attempt at writing a tool to mine the dumpped data.
#

import argparse
import collections
import glob
import os
import yaml


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
db["instance"] = {}
db["sg"] = {}
db["sg_instances"] = {}
db["sgr"] = {}


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
    if "GroupName" in db["sg"]:
        name = db["sg"]["GroupName"].lower()

    return f"{name} ({_id})"


def data_add_instance(_id, item):
    db["instance"][_id] = item
    for group in item.get("SecurityGroups",[]):
        groupid = group["GroupId"]
        db["sg_instances"].setdefault(groupid, set()).add(_id)


def data_add_sg(_id, item):
    db["sg"][_id] = item


def data_add_sgr(_id, item):
    db["sgr"][_id] = item


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

        # Clean up data we dont need to see at the moment
        del rule["GroupId"]
        del rule["GroupOwnerId"]
        del rule["SecurityGroupRuleArn"]
        del rule["SecurityGroupRuleId"]
        del rule['FromPort']
        del rule['ToPort']


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

        for instance in sorted(instances):
            print("Instance", instance)

        columns = sorted(str_table_columns(group))
        print(str_table(group, columns, orderby="CidrIpv4"))


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
            if raw["datatype"] == "aws.ec2.security_group_rules":
                data_add_sgr(_id, item)
                continue
            if raw["datatype"] == "aws.ec2.security_groups":
                data_add_sg(_id, item)
                continue


def main():
    args = argparser()

    load_data(args)
    dump_all_sg()


if __name__ == "__main__":
    main()
