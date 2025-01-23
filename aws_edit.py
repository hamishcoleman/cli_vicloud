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


subc_list = {}


def CLI(*_args, **kwargs):
    def wrap(f):
        entry = {
            "_final": True,
            "func": f,
            "help": f.__doc__,
        }
        entry.update(kwargs)
        args = list(_args)

        curr_level = subc_list
        while args:
            subc = args.pop(0)
            if not args:
                # this is the terminal subc level
                if subc in curr_level:
                    raise ValueError(f"Duplicate action {subc}")

                curr_level[subc] = entry
                return f

            # this is still a prefix
            if subc not in curr_level:
                curr_level[subc] = {}

            curr_level = curr_level[subc]

            if "_final" in curr_level:
                raise ValueError(f"both final and non final at {subc}")

        # should never get here
        raise ValueError("unknown")

    return wrap


@CLI("ec2","tags")
def subc_ec2_tags(args):
    """Edit ec2 tags"""

    print("ec2 tags")
    print(args)


def argparser_subc(argp, subc_list):
    subc = argp.add_subparsers(
        dest="command",
        help="Command",
    )

    for name, data in sorted(subc_list.items()):
        if "_final" not in data:
            cmd = subc.add_parser(name)
            argparser_subc(cmd, data)
            continue

        arg = False
        if "arg" in data and data["arg"]:
            arg = data["arg"]

        cmd = subc.add_parser(name, help=data["help"])
        cmd.set_defaults(func=data["func"])
        if arg:
            cmd.add_argument(arg, nargs="*")

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

    

    result = args.func(args)
    if result is not None:
        print(result)


if __name__ == "__main__":
    main()
