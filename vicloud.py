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
import csv
import os
import subprocess
import sys
import yaml

# Ensure that we look for any modules in our local lib dir.  This allows simple
# testing and development use.  It also does not break the case where the lib
# has been installed properly on the normal sys.path
sys.path.insert(
    0,
    os.path.join(os.path.dirname(os.path.realpath(__file__)), 'lib')
)
# I would use site.addsitedir, but it does an append, not insert

import aws.ec2  # noqa


def output_data_csv(data, file):
    fields = sorted(data.fields())
    writer = csv.DictWriter(file, fieldnames=fields)
    writer.writeheader()
    for row in data.rows():
        writer.writerow(row)


def output_data_vd(data):
    child = subprocess.Popen(
        ["vd", "-f", "csv", "-"],
        stdin=subprocess.PIPE,
        text=True
    )
    output_data_csv(data, child.stdin)
    child.stdin.close()
    child.wait()


def output_data_yaml(data, file):
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
    print(yamlstr, file=file)


def process_data(args, data):
    # TODO:
    # if show table ..
    # if edit ..
    # output file name

    if args.mode == "csv":
        output_data_csv(data, sys.stdout)
        return

    if args.mode == "vd":
        output_data_vd(data)
        return

    if args.mode == "yaml":
        output_data_yaml(data, sys.stdout)
        return


subc_list = {
    "ec2": {
        "help": "Deal with EC2 objects",
        "subc": {
            "account_attributes": {
                "handler": aws.ec2.account_attributes_handler,
            },
            "availability_zones": {
                "handler": aws.ec2.availability_zones_handler,
            },
            "instances": {
                "handler": aws.ec2.instances_handler,
            },
            "tags": {
                "handler": aws.ec2.tags_handler,
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

        # TODO:
        # - if no datatype to fetch is specified, assume this is an apply?

    handler = args.handler()

    sessions = aws.ec2.setup_sessions(args.profile, args.region)

    data = handler.fetch(args, sessions)
    if data is None:
        print("No data")
        return

    if args.verbose > 1:
        print(data)

    process_data(args, data)


if __name__ == "__main__":
    main()
