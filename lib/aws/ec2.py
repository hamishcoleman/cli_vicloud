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


class _data_two_deep(base):
    """Generic parser for simple structure with two layers"""
    def _fetch_one_client(self, client):
        data = {}

        for r1 in self._paged_op(client, self.operator):
            for r2 in r1[self.r1_key]:
                _id = r2[self.r2_id]
                data[_id] = r2

        return data


class account_attributes(base):
    datatype = "aws.ec2.account_attributes"

    def _fetch_one_client(self, client):
        data = {}
        operator = "describe_account_attributes"
        r1_key = "AccountAttributes"

        for r1 in self._paged_op(client, operator):
            for r2 in r1[r1_key]:
                k = r2["AttributeName"]

                values = []
                for value in r2["AttributeValues"]:
                    values.append(value["AttributeValue"])

                data[k] = ",".join(values)

        return {0: data}


class availability_zones(_data_two_deep):
    datatype = "aws.ec2.availability_zones"
    operator = "describe_availability_zones"
    r1_key = "AvailabilityZones"
    r2_id = "ZoneId"


class dhcp_options(base):
    datatype = "aws.ec2.dhcp_options"

    def _fetch_one_client(self, client):
        data = {}
        operator = "describe_dhcp_options"
        r1_key = "DhcpOptions"
        r2_id = "DhcpOptionsId"

        for r1 in self._paged_op(client, operator):
            for r2 in r1[r1_key]:
                _id = r2[r2_id]
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


class host_reservation_offerings(_data_two_deep):
    datatype = "aws.ec2.host_reservation_offerings"
    operator = "describe_host_reservation_offerings"
    r1_key = "OfferingSet"
    r2_id = "OfferingId"


class images(_data_two_deep):
    datatype = "aws.ec2.images"
    operator = "describe_images"
    r1_key = "Images"
    r2_id = "ImageId"


class instances(base):
    datatype = "aws.ec2.instances"

    def _fetch_one_client(self, client):
        data = {}
        operator = "describe_instances"
        r1_key = "Reservations"
        r2_key = "Instances"
        r3_id = "InstanceId"

        for r1 in self._paged_op(client, operator):
            for r2 in r1[r1_key]:
                for r3 in r2[r2_key]:
                    _id = r3[r3_id]
                    data[_id] = r3

        return data


class tags(base):
    """Edit ec2 tags"""
    datatype = "aws.ec2.tags"

    def _fetch_one_client(self, client):
        data = {}
        operator = "describe_tags"
        r1_key = "Tags"
        r2_id = "ResourceId"

        for r1 in self._paged_op(client, operator):
            for r2 in r1[r1_key]:
                _id = r2[r2_id]
                k = r2["Key"]
                v = r2["Value"]

                if _id not in data:
                    data[_id] = {}

                data[_id][k] = v

        return data
