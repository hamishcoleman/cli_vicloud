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
import inspect
import json
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

import aws      # noqa
import aws.ec2  # noqa
import aws.eks  # noqa
import aws.elb  # noqa
import aws.iam  # noqa


def output_data_csv(data, file):
    fields = sorted(data.fields())
    writer = csv.DictWriter(file, fieldnames=fields)
    writer.writeheader()
    for row in data.rows():
        writer.writerow(row)


def output_data_json(data, file):
    output = []
    for row in data.rows():
        output.append(row)
    json.dump(
        output,
        file,
        sort_keys=True,
        default=str,
    )


def output_data_vd(data, mode):
    child = subprocess.Popen(
        ["vd", "-f", mode, "-"],
        stdin=subprocess.PIPE,
        text=True
    )
    if mode == "csv":
        output_data_csv(data, child.stdin)
    elif mode == "json":
        output_data_json(data, child.stdin)
    else:
        raise ValueError(f"unknown vd mode {mode}")

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

    if args.mode == "json":
        output_data_json(data, sys.stdout)
        return

    if args.mode == "vd":
        output_data_vd(data, args.mode_vd)
        return

    if args.mode == "yaml":
        output_data_yaml(data, sys.stdout)
        return


subc_list = {
    "ec2": {
        "help": "Virtual machines (Elastic Compute Cloud)",
    },
    "eks": {
        "help": "Elastic K8s Service",
    },
    "elb": {
        "help": "Elastic Load Balancer",
    },
    "iam": {
        "help": "Users and Perms (IAM)",
    },
}


def argparser_populate_subc(subc, module, prefix):
    if "subc" not in subc:
        subc["subc"] = {}

    """Inspect the given module for handlers to add to the subc"""
    for name, obj in inspect.getmembers(module):
        if not inspect.isclass(obj):
            # only care about classes
            continue
        if not hasattr(obj, "datatype"):
            # only care about ones with a datatype
            continue
        if not obj.datatype.startswith(prefix):
            # just want the specified datatype prefix
            continue

        name = obj.datatype[len(prefix):]

        if name in subc["subc"]:
            raise ValueError(f"duplicate subc {name}")

        subc["subc"][name] = {}
        subc["subc"][name]["handler"] = obj


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
        default=1,
        help="Increase verbosity",
    )
    args.add_argument(
        "-q", "--quiet",
        action='store_true',
        default=False,
        help="Set verbosity to zero",
    )
    # dry run?

    args.add_argument(
        "--mode",
        choices=[
            "csv",
            "json",
            "vd",
            "yaml",
        ],
        default="vd",
        help="What to do with the data",
    )
    args.add_argument(
        "--mode_vd",
        choices=[
            "csv",
            "json",
        ],
        default="json",
        help="What data type to send to vd",
    )

    argparser_subc(args, subc_list)

    r = args.parse_args()

    if r.quiet:
        r.verbose = 0

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
    argparser_populate_subc(subc_list["ec2"], aws.ec2, "aws.ec2.")
    argparser_populate_subc(subc_list["eks"], aws.eks, "aws.eks.")
    argparser_populate_subc(subc_list["elb"], aws.elb, "aws.elbv2.")
    argparser_populate_subc(subc_list["iam"], aws.iam, "aws.iam.")
    args = argparser()

    if not args.command:
        print("Need command")
        return

        # TODO:
        # - if no datatype to fetch is specified, assume this is an apply?

    handler = args.handler()
    handler.verbose = args.verbose

    sessions = aws.setup_sessions(args.verbose, args.profile, args.region)

    data = handler.fetch(args, sessions)
    if data is None:
        print("No data")
        return

    if args.verbose > 1:
        print(data)

    process_data(args, data)


if __name__ == "__main__":
    main()
