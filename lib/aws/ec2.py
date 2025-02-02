import boto3
import definitionset


def setup_sessions(profiles, regions):
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


class base:
    def fetch(self, args, sessions):
        db = definitionset.DefinitionSet()
        for session in sessions:
            # TODO
            # if not quiet
            #  print stderr profile/region

            resultset = definitionset.Definition()
            resultset.datatype = self.datatype
            resultset.region = session["region"]
            resultset.session = session["session"]

            client = resultset.session.client(
                "ec2",
                region_name=resultset.region,
            )

            specifics = self._fetch_one_client(client)
            if specifics:
                resultset.data = specifics
                db.append(resultset)

        return db

    def _fetch_one_client(self, client):
        raise NotImplementedError

    def apply(self, data):
        raise NotImplementedError

    @classmethod
    def _paged_op(cls, client, operation):
        """Wrap possible pagination in a helper"""

        if not client.can_paginate(operation):
            operator = getattr(client, operation)
            yield operator()
        else:
            token = None
            paginator = client.get_paginator(operation)

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
                yield page


class account_attributes_handler(base):
    datatype = "aws.ec2.account_attributes"

    def _fetch_one_client(self, client):
        data = {}
        r = client.describe_account_attributes()

        attributes = r["AccountAttributes"]
        for attr in attributes:
            k = attr["AttributeName"]

            values = []
            for value in attr["AttributeValues"]:
                values.append(value["AttributeValue"])

            data[k] = ",".join(values)

        return {0: data}


class availability_zones_handler(base):
    datatype = "aws.ec2.availability_zones"

    def _fetch_one_client(self, client):
        data = {}
        r = client.describe_availability_zones()

        r2 = r["AvailabilityZones"]
        for r3 in r2:
            _id = r3["ZoneId"]
            data[_id] = r3

        return data


class dhcp_options_handler(base):
    datatype = "aws.ec2.dhcp_options"

    def _fetch_one_client(self, client):
        data = {}
        for r1 in self._paged_op(client, "describe_dhcp_options"):
            for r2 in r1["DhcpOptions"]:
                _id = r2["DhcpOptionsId"]
                if _id not in data:
                    data[_id] = {}
                data[_id]["OwnerId"] = r2["OwnerId"]
                data[_id]["Tags"] = r2["Tags"]

                for r3 in r2["DhcpConfigurations"]:
                    k = r3["Key"]

                    values = []
                    for value in r3["Values"]:
                        values.append(value["Value"])

                    data[_id][k] = ",".join(values)

        return data


class host_reservation_offerings_handler(base):
    datatype = "aws.ec2.host_reservation_offerings"

    def _fetch_one_client(self, client):
        data = {}
        operator = "describe_host_reservation_offerings"
        for r1 in self._paged_op(client, operator):
            for r2 in r1["OfferingSet"]:
                _id = r2["OfferingId"]
                data[_id] = r2

        return data


class images_handler(base):
    datatype = "aws.ec2.images"

    def _fetch_one_client(self, client):
        data = {}
        operator = "describe_images"
        for r1 in self._paged_op(client, operator):
            for r2 in r1["Images"]:
                _id = r2["ImageId"]
                data[_id] = r2

        return data


class instances_handler(base):
    datatype = "aws.ec2.instances"

    def _fetch_one_client(self, client):
        specifics = {}
        for page in self._paged_op(client, "describe_instances"):
            reservations = page["Reservations"]
            for reservation in reservations:
                instances = reservation["Instances"]
                for instance in instances:
                    _id = instance["InstanceId"]
                    specifics[_id] = instance

        return specifics


class tags_handler(base):
    """Edit ec2 tags"""
    datatype = "aws.ec2.tags"

    def _fetch_one_client(self, client):
        specifics = {}
        for page in self._paged_op(client, "describe_tags"):
            tags = page["Tags"]
            for tag in tags:
                _id = tag["ResourceId"]
                k = tag["Key"]
                v = tag["Value"]

                if _id not in specifics:
                    specifics[_id] = {}

                specifics[_id][k] = v

        return specifics
