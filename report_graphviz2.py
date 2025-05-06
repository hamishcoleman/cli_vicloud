#!/usr/bin/env python3
"""Generate a useable diagram of AWS components"""
#
#

import argparse
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
        help="Which directory to scan for data files",
    )

    r = args.parse_args()
    return r


db = {}
db["instance"] = {}
db["network_interface"] = {}
db["subnet"] = {}
db["vpc"] = {}

db["index_vpc_subnet"] = {}
db["index_subnet_instance"] = {}


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


def _tagged_name(_id, _type):
    if _id not in db[_type]:
        raise ValueError(f"Unknown {_id} {_type}")

    name = _id
    for tag in db[_type][_id].get("Tags", []):
        if tag["Key"] != "Name":
            continue
        name = tag["Value"].lower()

    return name


def str_instance_name(_id):
    return _tagged_name(_id, "instance")


def str_subnet_name(_id):
    return _tagged_name(_id, "subnet")


def str_vpc_name(_id):
    return _tagged_name(_id, "vpc")


def data_add_instance(_id, item):
    db["instance"][_id] = item
    subnetid = item["SubnetId"]
    index = db["index_subnet_instance"].setdefault(subnetid, [])
    index.append(_id)


def data_add_network_interface(_id, item):
    db["network_interface"][_id] = item


def data_add_subnet(_id, item):
    db["subnet"][_id] = item
    db["index_subnet_instance"].setdefault(_id, [])

    vpcid = item["VpcId"]
    index = db["index_vpc_subnet"].setdefault(vpcid, [])
    index.append(_id)


def data_add_vpc(_id, item):
    db["vpc"][_id] = item


def load_data(args):

    loaders = {
        "aws.ec2.instances": data_add_instance,
        "aws.ec2.network_interfaces": data_add_network_interface,
        "aws.ec2.subnets": data_add_subnet,
        "aws.ec2.vpcs": data_add_vpc,
    }

    os.chdir(args.dirname)
    for filename in glob.glob("**/*.yaml", recursive=True):
        with open(filename, "r+") as f:
            raw = yaml.safe_load(f)
            if args.profile and raw["metadata"]["profile"] not in args.profile:
                continue
            if args.region and raw["metadata"]["region"] not in args.region:
                continue

            datatype = raw["datatype"]
            _id = raw["metadata"]["resourceid"]
            item = raw["specifics"]

            if datatype in loaders:
                loaders[datatype](_id, item)
                continue


def dump_graphviz():
    print("graph G {")
    print(" node [ shape=record ]")
    # print(" rankdir = LR")
    print(" rankdir = TB")
    print(" pack=true")

    for vpcid, vpc in db["vpc"].items():
        name = str_vpc_name(vpcid)
        print(f' subgraph "cluster_{name}" {{')
        print(f'  label="{name}"')

        for subnetid in db["index_vpc_subnet"][vpcid]:
            subnet = db["subnet"][subnetid]
            subnet_name = str_subnet_name(subnetid)
            print(f'  subgraph "cluster_{subnet_name}" {{')
            print(f'   label="{subnet_name}\\n{subnet["CidrBlock"]}"')

            for instanceid in db["index_subnet_instance"][subnetid]:
                instance = db["instance"][instanceid]
                instance_name = str_instance_name(instanceid)

                nodelines = []

                # TODO: support multiple interfaces/addresses per instance
                _pub = instance.get("PublicIpAddress", None)
                _prv = instance.get("PrivateIpAddress", None)

                if _pub:
                    nodelines.append(f"{_pub}")
                else:
                    nodelines.append("")
                if _prv:
                    nodelines.append(f"{_prv}")
                else:
                    nodelines.append("")
                nodelines.append(instance_name)

                print(
                    f'   "{instance_name}" [label="{{{"|".join(nodelines)}}}"]'
                )

            print("  }")

        print(" }")

    print("}")


def main():
    args = argparser()

    load_data(args)

    dump_graphviz()


if __name__ == "__main__":
    main()
