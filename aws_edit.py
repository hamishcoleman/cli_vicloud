#!/usr/bin/env python3
"""View, Edit, Apply AWS configurations
"""
#
# :dotsctl:
#   destdir: ~/bin/
#   dpkg:
#     - python3-boto3
#     - python3-yaml
# ...

import argparse
import boto3
import collections
import io
import os
import subprocess
import sys
import tempfile
import yaml


def aws_setup_all(profiles, regions):
    # TODO:
    # - support "all" profiles with client.list_profiles()

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

        for region in regions:
            this = {
                "profile": profile,
                "region": region,
                "session": session,
            }
            sessions.append(this)

    return sessions


def subc_ec2_tags(args, sessions):
    """Edit ec2 tags"""

    print("ec2 tags")
    print(args)


subc_list = {
    "ec2": {
        "help": "Deal with EC2 objects",
        "subc": {
            "tags": {
                "handler": subc_ec2_tags,
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

    argparser_subc(args, subc_list)

    r = args.parse_args()

    profiles = []
    for profile in r.profile:
        profiles.append(region.split(","))
    r.profile = profiles

    regions = []
    for region in r.region:
        regions.append(region.split(","))
    r.region = regions

    return r


def main():
    args = argparser()

    if not args.command:
        print("Need command")
        return

        # TODO: a default command?

    sessions = aws_setup_all(args.profile, args.region)

    result = args.handler(args, sessions)
    if result is None:
        print("No results")
        return

    print(result)
    # if show table ..
    # if vd ..
    # if edit ..



if __name__ == "__main__":
    main()
