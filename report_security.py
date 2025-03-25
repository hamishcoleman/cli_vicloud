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


def main():
    args = argparser()
    rules = {}

    os.chdir(args.dirname)
    for filename in glob.glob("**/*.yaml", recursive=True):
        with open(filename, "r+") as f:
            raw = yaml.safe_load(f)
            if args.profile and raw["metadata"]["profile"] not in args.profile:
                continue
            if args.region and raw["metadata"]["region"] not in args.region:
                continue

            if raw["datatype"] != "aws.ec2.security_group_rules":
                continue

            _id = raw["metadata"]["resourceid"]
            item = raw["specifics"]
            rules[_id] = item

    groups = {}
    for rule in rules.values():
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

    for _id in sorted(groups.keys()):
        group = groups[_id]
        print()
        print("GroupId:", _id)

        columns = sorted(str_table_columns(group))
        print(str_table(group, columns, orderby="CidrIpv4"))


if __name__ == "__main__":
    main()
