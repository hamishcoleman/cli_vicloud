#!/usr/bin/env python3
"""View, Edit, Apply AWS configurations
"""
#
# :dotsctl:
#   destdir: ~/bin/
#   dpkg:
#     - python3-boto3
#     - python3-yaml
#     - visidata
# ...

import argparse
import boto3
import collections
import csv
import io
import os
import subprocess
import sys
import tempfile
import yaml


class Definition:
    """Encapsulate the data needed to describe the remote object"""
    def __init__(self):
        # Set defaults for the metadata
        self.datatype = None
        self.region = None
        self.session = None

        # Initialise with empty data
        self.data = None

    def __repr__(self):
        return str(self.__dict__)

    def fields(self):
        """Return the field names of both metadata and data"""
        d = set()
        d.add("@DataType")
        d.add("@Profile")
        d.add("@Region")
        d.add("@ResourceId")

        for _id, row in self.data.items():
            d.update(row)

        return d

    def rows(self):
        """Yield the contents (with metadata added)"""

        for _id, row in self.data.items():
            this = {}
            this["@DataType"] = self.datatype
            this["@Profile"] = self.session.profile_name
            this["@Region"] = self.region
            this["@ResourceId"] = _id
            this.update(row)
            yield this


class DefinitionSet:
    """A list of definitions"""
    def __init__(self):
        self._list = []

    def __repr__(self):
        return str(self._list)

    def append(self, data):
        self._list.append(data)

    def fields(self):
        """Return the combined field names of all the definitions"""
        d = set()
        for data in self._list:
            d.update(data.fields())
        return d

    def rows(self):
        """Yield the contents"""
        for data in self._list:
            for row in data.rows():
                yield row


class aws_ec2_tags_handler:
    """Edit ec2 tags"""

    def fetch(self, args, sessions):
        db = DefinitionSet()
        for session in sessions:
            # TODO
            # if not quiet
            #  print stderr profile/region

            resultset = Definition()
            resultset.datatype = "aws.ec2.tags"
            resultset.region = session["region"]
            resultset.session = session["session"]
            data = {}

            client = resultset.session.client(
                "ec2",
                region_name=resultset.region,
            )

            token = None
            paginator = client.get_paginator("describe_tags")

            response = paginator.paginate(
                PaginationConfig={
                    "PageSize": 50,
                    "StartingToken": token,
                }
            )

            for page in response:
                # TODO
                # if not quiet and enough tags since last print
                #   print stderr fetching ...
                tags = page["Tags"]
                for tag in tags:
                    _id = tag["ResourceId"]
                    k = tag["Key"]
                    v = tag["Value"]

                    if _id not in data:
                        data[_id] = {}

                    data[_id][k] = v

            if data:
                resultset.data = data
                db.append(resultset)

        return db

    def apply(self, data):
        pass


def process_data_csv(data, file):
    fields = sorted(data.fields())
    writer = csv.DictWriter(file, fieldnames=fields)
    writer.writeheader()
    for row in data.rows():
        writer.writerow(row)


def process_data_vd(data):
    child = subprocess.Popen(
        ["vd", "-f", "csv", "-"],
        stdin=subprocess.PIPE,
        text=True
    )
    process_data_csv(data, child.stdin)
    child.stdin.close()
    child.wait()


def process_data_yaml(data):
    # TODO:
    # - use an accessor for the DefinitionSet list
    # - use an accessor for the Definition data

    output = []
    for group in data._list:
        for _id, item in group.data.items():
            this = {}
            this["datatype"] = group.datatype
            this["metadata"] = {}
            this["metadata"]["profile"] = group.session.profile_name
            this["metadata"]["region"] = group.region

            # TODO: this will probably not be generic for other datatypes
            this["metadata"]["resourceid"] = _id

            this["specifics"] = item

            output.append(this)

    yamlstr = yaml.safe_dump_all(
        output,
        explicit_start=True,
        explicit_end=True,
        default_flow_style=False,
        sort_keys=True,
    )
    print(yamlstr)


def process_data(args, data):
    # TODO:
    # if show table ..
    # if edit ..
    # output file name

    if args.mode == "csv":
        process_data_csv(data, sys.stdout)
        return

    if args.mode == "vd":
        process_data_vd(data)
        return

    if args.mode == "yaml":
        process_data_yaml(data)
        return


def aws_setup_all(profiles, regions):
    sessions = []

    if not profiles:
        profiles = [None]

    for profile in profiles:
        session = boto3.Session(profile_name=profile)

        if not regions:
            # Get the list of regions enabled for our profile
            client = session.client("ec2", region_name="us-west-2")
            reply = client.describe_regions()
            this_regions = [r['RegionName'] for r in reply['Regions']]
        else:
            this_regions = regions

        for region in this_regions:
            this = {
                "region": region,
                "session": session,
            }
            sessions.append(this)

    return sessions


subc_list = {
    "ec2": {
        "help": "Deal with EC2 objects",
        "subc": {
            "tags": {
                "handler": aws_ec2_tags_handler,
            },
        },
    },
}


def argparser_subc(argp, subc_list):
    subp = argp.add_subparsers(
        dest="command",
        help="Command",
    )

    for name, data in sorted(subc_list.items()):
        if "handler" in data:
            help = data["handler"].__doc__
        else:
            help = data["help"]
        cmd = subp.add_parser(name, help=help)

        if "handler" in data:
            cmd.set_defaults(handler=data["handler"])

        if "subc" in data:
            argparser_subc(cmd, data["subc"])


def argparser():
    args = argparse.ArgumentParser(
        description=__doc__,
    )

    args.add_argument(
        "--profile",
        action="append",
        default=[],
        help="Select which awscli profile to use",
    )
    args.add_argument(
        "--region",
        action="append",
        default=[],
        help="Restrict queries to this region only (default is all regions)",
    )
    args.add_argument(
        "-v", "--verbose",
        action='count',
        default=0,
        help="Increase verbosity",
    )
    # quiet?
    # dry run?

    args.add_argument(
        "--mode",
        choices=[
            "csv",
            "vd",
            "yaml",
        ],
        default="vd",
        help="What to do with the data",
    )

    argparser_subc(args, subc_list)

    r = args.parse_args()

    profiles = []
    for profile in r.profile:
        profiles += profile.split(",")
    r.profile = profiles

    regions = []
    for region in r.region:
        regions += region.split(",")
    r.region = regions

    return r


def main():
    args = argparser()

    if not args.command:
        print("Need command")
        return

        # TODO: a default command?

    handler = args.handler()

    sessions = aws_setup_all(args.profile, args.region)

    data = handler.fetch(args, sessions)
    if data is None:
        print("No data")
        return

    if args.verbose > 1:
        print(data)

    process_data(args, data)


if __name__ == "__main__":
    main()
