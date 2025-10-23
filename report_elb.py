#!/usr/bin/env python3
"""Summarise a set of ELB yaml files"""
#
# An initial attempt at writing a tool to mine the dumpped data.
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
        "--show_all_hosts",
        action="store_true",
        default=False,
        help="Always show hosts, even if they have no ELB connections",
    )

    args.add_argument(
        "--cloudflare_yaml",
        type=argparse.FileType('r'),
        action="append",
        default=[],
        help="File to load DNS data from",
    )

    args.add_argument(
        "dirname",
        help="Which directory to scan for SGR items",
    )

    r = args.parse_args()
    return r


class ItemBase:
    @classmethod
    def get(cls, arn):
        return cls.db[arn]

    def __init__(self, data):
        self.data = data
        arn = self.arn()
        self.db[arn] = self

    def arn(self):
        return self.data[self._arn_key]

    def name(self):
        """A short human readable name"""
        return self.data[self._name_key]

    def key(self):
        """A unique key. eg - name of graphviz objects"""
        return f"{type(self).__name__}_{self.data[self._key_key]}"

    def graphviz_node(self):
        """Return the graphviz node definition"""
        return f'"{self.key()}" [ label="{self.name()}" ]'

    def graphviz_edges(self):
        raise NotImplementedError()


class DNS(ItemBase):
    db = {}
    _key_key = "name"
    _name_key = "name"

    def __init__(self, data):
        self.data = data
        self.db[self.name()] = self
        self.ref = None

    def ref_bind(self):
        """Lookup what this DNS entry is referencing to and bind to it"""
        item = None
        if self.data["type"] == "CNAME":
            try:
                item = Load_Balancer.lookup_fqdn(self.data["content"])
            except KeyError:
                # TODO: print warning
                pass

            # TODO: if not found in load balancers, lookup fqdn in instances

        if self.data["type"] == "A":
            try:
                item = Instance.lookup_ipaddr(self.data["content"])
            except KeyError:
                # TODO: print warning
                pass

        if item is not None:
            self.ref = item
            item.add_dns_ref(self)

    def graphviz_node(self):
        if self.data["type"] not in ["A", "CNAME"]:
            # We are not (currently) interested in the other things here
            return ""
        return f'"{self.key()}" [ shape=cds label="{self.name()}" ]'

    def graphviz_edges(self):
        if self.ref is not None:
            return f'"{self.key()}" -> "{self.ref.key()}"'

        return ""


class Load_Balancer(ItemBase):
    db = {}
    db_fqdn = {}
    _arn_key = "LoadBalancerArn"
    _key_key = "LoadBalancerName"
    _name_key = "LoadBalancerName"

    @classmethod
    def lookup_fqdn(cls, fqdn):
        return cls.db_fqdn[fqdn]

    def __init__(self, data):
        super().__init__(data)
        self.db_fqdn[self.fqdn()] = self
        self.listeners = {}
        self.target_groups = {}
        self.dns_ref = False

    def add_dns_ref(self, item):
        self.dns_ref = True

    def add_listener(self, item):
        arn = item.arn()
        self.listeners[arn] = item

    def add_target_group(self, item):
        arn = item.arn()
        self.target_groups[arn] = item

    def fqdn(self):
        return self.data["DNSName"]

    def graphviz_node(self):
        r = []
        r += [f'subgraph "cluster_{self.key()}" {{']
        r += [f'  label="{self.name()}"']
        if self.dns_ref:
            # If we have been told that someone refers to use via our DNS, we
            # need to create a handle for the edges to attach to
            r += [f'  "{self.key()}" [ label="dns" ]']
        r += [""]
        for item_arn in sorted(self.listeners.keys()):
            item = self.listeners[item_arn]
            r += [item.graphviz_node()]
        r += [""]
        for item_arn in sorted(self.target_groups.keys()):
            item = self.target_groups[item_arn]
            r += [item.graphviz_node()]
        r += ["}"]

        return "\n".join(r)


class Listener(ItemBase):
    db = {}
    _arn_key = "ListenerArn"

    def __init__(self, data):
        super().__init__(data)
        self.rules = {}

    def add_rule(self, item):
        arn = item.arn()
        self.rules[arn] = item

    def elb_arn(self):
        return self.data["LoadBalancerArn"]

    def elb_bind(self):
        try:
            elb = Load_Balancer.get(self.elb_arn())
            elb.add_listener(self)
        except KeyError:
            # TODO: print warning
            pass

    def _elb_name(self):
        """return a friendly name for our attached ELB"""
        arn = self.arn()
        fields = arn.split("/")
        assert fields[0].endswith("listener")
        return fields[2]

    def name(self):
        port = self.data["Port"]
        protocol = self.data["Protocol"]
        return f"{protocol}:{port}"

    def key_fragment(self):
        """The key without the type, used by child Rules"""
        return f"{self._elb_name()}_{self.name()}"

    def key(self):
        return f"{type(self).__name__}_{self.key_fragment()}"

    def graphviz_node(self):
        r = []
        r += [super().graphviz_node()]
        for rule in self.rules.values():
            r += [rule.graphviz_node()]

        return "\n".join(r)

    def graphviz_edges(self):
        r = []

        rules = self.rules.values()
        for rule in rules:
            r += [rule.graphviz_edges()]

        if not len(rules):
            # If for some reason we dont have the rules data, we can at least
            # use the default action information inside the listener object
            #
            # TODO: this duplicates the interpretation in the Rules renderer

            key = self.key()

            for action in self.data["DefaultActions"]:
                if action["Type"] == "redirect":
                    redir = action["RedirectConfig"]
                    proto = redir["Protocol"]
                    host = redir["Host"]
                    port = redir["Port"]
                    dest = f'{proto}://{host}:{port}'
                elif action["Type"] == "forward":
                    target_arn = action["TargetGroupArn"]
                    try:
                        target_group = Target_Group.get(target_arn)
                        dest = target_group.key()
                    except KeyError:
                        dest = target_arn

                r += [f'"{key}" -> "{dest}"']

        return "\n".join(r)


class Rules(ItemBase):
    db = {}
    _arn_key = "RuleArn"

    def key(self):
        listener = Listener.get(self.listener_arn())
        return f"{type(self).__name__}_{listener.key_fragment()}"

    def listener_arn(self):
        try:
            return self.data["_listener_arn"]
        except KeyError:
            return "FIXME_old_dump_data"

    def listener_bind(self):
        listener_arn = self.listener_arn()
        try:
            listener = Listener.get(listener_arn)
            listener.add_rule(self)
        except KeyError:
            # TODO: print warning
            pass

    def graphviz_node(self):
        r = []

        # Only need nodes for some types of actions
        for action in self.data["Actions"]:
            if action["Type"] == "fixed-response":
                key = f"{self.key()}_fixed-response"
                r += [f'"{key}" [ label="fixed-response" ]']

        return "\n".join(r)

    def graphviz_edges(self):
        r = []
        listener = Listener.get(self.listener_arn())
        src = listener.key()

        for action in self.data["Actions"]:
            if action["Type"] == "forward":
                target_arn = action["TargetGroupArn"]
                try:
                    target_group = Target_Group.get(target_arn)
                    dest = target_group.key()
                except KeyError:
                    dest = target_arn
            elif action["Type"] == "redirect":
                redir = action["RedirectConfig"]
                dest = f'{redir["Protocol"]}://{redir["Host"]}:{redir["Port"]}'
            elif action["Type"] == "fixed-response":
                dest = f"{self.key()}_fixed-response"

            # implicitly else raise NameError: dest is not defined

            r += [f'"{src}" -> "{dest}"']

        return "\n".join(r)


class Target_Group(ItemBase):
    db = {}
    _arn_key = "TargetGroupArn"
    _key_key = "TargetGroupName"
    _name_key = "TargetGroupName"

    def __init__(self, data):
        super().__init__(data)
        self.target_health = {}

    def elb_arn(self):
        assert len(self.data["LoadBalancerArns"]) <= 1
        return self.data["LoadBalancerArns"][0]

    def elb_bind(self):
        try:
            elb = Load_Balancer.get(self.elb_arn())
            elb.add_target_group(self)
        except (IndexError, KeyError):
            # TODO: print warning
            pass

    def add_target_health(self, item):
        self.target_health = item

    def graphviz_edges(self):
        r = []
        key = self.key()
        registered = self.target_health.data["TargetHealthDescriptions"]
        for item_key in sorted(registered.keys()):
            item = registered[item_key]
            target = item["Target"]
            target_key = f'Target_Health_{target["Id"]}/{target["Port"]}'
            r += [f'"{key}" -> "{target_key}"']

        return "\n".join(r)


class Target_Health(ItemBase):
    db = {}
    _arn_key = "_arn"

    def group_arn(self):
        return self.data["_arn"]

    def group_bind(self):
        try:
            item = Target_Group.get(self.group_arn())
            item.add_target_health(self)
        except (KeyError):
            # TODO: print warning
            pass

    def instance_bind(self):
        for target in self.data["TargetHealthDescriptions"].values():
            target_id = target["Target"]["Id"]
            target_arn = f"FIXME:instance/{target_id}"
            try:
                instance = Instance.get(target_arn)
                instance.add_target_health(self)
            except KeyError:
                # TODO: print warning
                pass

    def graphviz_nodes(self, instance_id):
        r = []
        for target in self.data["TargetHealthDescriptions"].values():
            target_id = target["Target"]["Id"]

            # Only output the nodes for the current instance
            if target_id != instance_id:
                continue

            target_port = target["Target"]["Port"]

            clsname = type(self).__name__
            nodename = f"{clsname}_{target_id}/{target_port}"
            label = f"TCP/{target_port}"
            r += [f'"{nodename}" [ label="{label}" ]']
        return r


class Instance(ItemBase):
    db = {}
    db_ipaddr = {}
    _key_key = "InstanceId"

    @classmethod
    def lookup_ipaddr(cls, ipaddr):
        return cls.db_ipaddr[ipaddr]

    def __init__(self, data):
        super().__init__(data)
        public_ip_address = self.data.get("PublicIpAddress", None)
        if public_ip_address is not None:
            self.db_ipaddr[public_ip_address] = self
        self.target_health = {}
        self.dns_ref = False

    def add_dns_ref(self, item):
        self.dns_ref = True

    def arn(self):
        return f'FIXME:instance/{self.data["InstanceId"]}'

    def _tags_to_sane(self):
        tags = {}
        for tag in self.data["Tags"]:
            if tag["Key"] in tags:
                raise ValueError("Duplicate tag name")
            tags[tag["Key"]] = tag["Value"]

        stags = {}
        for k, v in sorted(tags.items()):
            stags[k] = v
        return stags

    def name(self):
        return self._tags_to_sane()["Name"]

    def graphviz_node(self, show_all_hosts=False):
        r = []
        r += [f'subgraph "cluster_{self.key()}" {{']
        label = self.name()
        if self.data["State"]["Name"] == "stopped":
            label += "\nSTOPPED"
            r += ["  color=red"]
        r += [f'  label="{label}"']
        if self.dns_ref:
            # If we have been told that someone refers to use via our DNS, we
            # need to create a handle for the edges to attach to
            r += [f'  "{self.key()}" [ label="dns" ]']
        r += [""]
        health = sorted(self.target_health.keys())
        for item_key in health:
            item = self.target_health[item_key]
            r += item.graphviz_nodes(self.data["InstanceId"])

        # A graphviz subgraph cluster with no nodes inside it is invisible
        # Show it if needed
        if not len(health) and show_all_hosts:
            r += [f'"{self.key()}"']

        r += ["}"]

        return "\n".join(r)

    def add_target_health(self, item):
        arn = item.arn()
        self.target_health[arn] = item


def dump_all_elb(show_all_hosts):
    print("digraph G {")
    print("  rankdir=LR")
    print("  node[shape=rectangle]")

    print()
    for elb_arn in sorted(Load_Balancer.db.keys()):
        elb = Load_Balancer.get(elb_arn)
        print(elb.graphviz_node())

    print()
    for item_arn in sorted(Instance.db.keys()):
        item = Instance.get(item_arn)
        print(item.graphviz_node(show_all_hosts=show_all_hosts))

    print()
    for listener_arn in sorted(Listener.db.keys()):
        listener = Listener.get(listener_arn)
        print(listener.graphviz_edges())

    print()
    for item_arn in sorted(Target_Group.db.keys()):
        item = Target_Group.get(item_arn)
        print(item.graphviz_edges())

    print()
    for item_key in sorted(DNS.db.keys()):
        item = DNS.get(item_key)
        print(item.graphviz_node())
        print(item.graphviz_edges())

    print("}")


def bind_data():
    """Several data types refer to each other, find them and bind them"""

    for item in Listener.db.values():
        item.elb_bind()

    for item in Target_Group.db.values():
        item.elb_bind()

    for item in Target_Health.db.values():
        item.group_bind()
        item.instance_bind()

    for item in Rules.db.values():
        item.listener_bind()

    for item in DNS.db.values():
        item.ref_bind()


def load_cloudflare_yaml(files):
    for fh in files:
        data = yaml.safe_load(fh)

        for item in data["result"]:
            DNS(item)


def load_data(args):
    os.chdir(args.dirname)
    for filename in glob.glob("**/*.yaml", recursive=True):
        with open(filename, "r+") as f:
            raw = yaml.safe_load(f)
            if args.profile and raw["metadata"]["profile"] not in args.profile:
                continue
            if args.region and raw["metadata"]["region"] not in args.region:
                continue

            datatype = raw["datatype"]
            item = raw["specifics"]

            if datatype == "aws.elbv2.load_balancers":
                Load_Balancer(item)
                continue

            if datatype == "aws.elbv2.listeners":
                Listener(item)
                continue

            if datatype == "aws.elbv2.target_groups":
                Target_Group(item)
                continue

            if datatype == "aws.elbv2.target_health":
                Target_Health(item)
                continue

            if datatype == "aws.elbv2.rules":
                Rules(item)
                continue

            if datatype == "aws.ec2.instances":
                Instance(item)
                continue


def main():
    args = argparser()

    if args.cloudflare_yaml is not None:
        load_cloudflare_yaml(args.cloudflare_yaml)

    load_data(args)
    bind_data()

    dump_all_elb(args.show_all_hosts)


if __name__ == "__main__":
    main()
