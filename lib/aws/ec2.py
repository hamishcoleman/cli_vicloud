import boto3
import botocore
import definitionset
import sys


def setup_sessions(verbose, profiles, regions):
    sessions = []

    if not profiles:
        session = boto3.Session()
        profiles = session.available_profiles

    for profile in profiles:
        session = boto3.Session(profile_name=profile)

        if not regions:
            # Get the list of regions enabled for our profile
            client = session.client("ec2", region_name="us-west-2")
            if verbose:
                print(f"{profile}: describe_regions", file=sys.stderr)

            try:
                reply = client.describe_regions()
                this_regions = [r['RegionName'] for r in reply['Regions']]
            except botocore.exceptions.ClientError:
                print(f"Error fetching regions for {profile}", file=sys.stderr)
                this_regions = []

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
    single_region = False

    def __init__(self):
        self.verbose = 0

    def fetch(self, args, sessions):
        db = definitionset.DefinitionSet()
        profiles_done = {}
        for session in sessions:
            profile_name = session["session"].profile_name
            if self.verbose:
                print(
                    f'{profile_name}:{session["region"]}: describe_tags',
                    file=sys.stderr
                )

            if self.single_region and profile_name in profiles_done:
                # skip all but the first region
                # TODO: use a cannonical region!
                continue
            profiles_done[profile_name] = True

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


class instance_credit_specifications(_data_two_deep):
    datatype = "aws.ec2.instance_credit_specifications"
    operator = "describe_instance_credit_specifications"
    r1_key = "InstanceCreditSpecifications"
    r2_id = "InstanceId"


class instance_types(_data_two_deep):
    datatype = "aws.ec2.instance_types"
    operator = "describe_instance_types"
    r1_key = "InstanceTypes"
    r2_id = "InstanceType"


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


class internet_gateways(_data_two_deep):
    datatype = "aws.ec2.internet_gateways"
    operator = "describe_internet_gateways"
    r1_key = "InternetGateways"
    r2_id = "InternetGatewayId"


class key_pairs(_data_two_deep):
    datatype = "aws.ec2.key_pairs"
    operator = "describe_key_pairs"
    r1_key = "KeyPairs"
    r2_id = "KeyPairId"


class managed_prefix_lists(_data_two_deep):
    datatype = "aws.ec2.managed_prefix_lists"
    operator = "describe_managed_prefix_lists"
    r1_key = "PrefixLists"
    r2_id = "PrefixListId"


# describe-nat-gateways
# describe-network-acls
# describe-network-interface-permissions


class network_interfaces(_data_two_deep):
    datatype = "aws.ec2.network_interfaces"
    operator = "describe_network_interfaces"
    r1_key = "NetworkInterfaces"
    r2_id = "NetworkInterfaceId"


class prefix_lists(_data_two_deep):
    datatype = "aws.ec2.prefix_lists"
    operator = "describe_prefix_lists"
    r1_key = "PrefixLists"
    r2_id = "PrefixListId"


class regions(_data_two_deep):
    datatype = "aws.ec2.regions"
    operator = "describe_regions"
    single_region = True
    r1_key = "Regions"
    r2_id = "RegionName"


class route_tables(_data_two_deep):
    datatype = "aws.ec2.route_tables"
    operator = "describe_route_tables"
    r1_key = "RouteTables"
    r2_id = "RouteTableId"


class security_group_rules(_data_two_deep):
    datatype = "aws.ec2.security_group_rules"
    operator = "describe_security_group_rules"
    r1_key = "SecurityGroupRules"
    r2_id = "SecurityGroupRuleId"


class snapshots(_data_two_deep):
    datatype = "aws.ec2.snapshots"
    operator = "describe_snapshots"
    r1_key = "Snapshots"
    r2_id = "SnapshotId"


class subnets(_data_two_deep):
    datatype = "aws.ec2.subnets"
    operator = "describe_subnets"
    r1_key = "Subnets"
    r2_id = "SubnetId"


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


# describe-transit-gateway-attachments
# describe-transit-gateway-connect-peers
# describe-transit-gateway-connects
# describe-transit-gateway-multicast-domains
# describe-transit-gateway-peering-attachments
# describe-transit-gateway-policy-tables
# describe-transit-gateway-route-table-announcements
# describe-transit-gateway-route-tables
# describe-transit-gateway-vpc-attachments
# describe-transit-gateways


class volume_status(_data_two_deep):
    datatype = "aws.ec2.volume_status"
    operator = "describe_volume_status"
    r1_key = "VolumeStatuses"
    r2_id = "VolumeId"


class volumes(_data_two_deep):
    datatype = "aws.ec2.volumes"
    operator = "describe_volumes"
    r1_key = "Volumes"
    r2_id = "VolumeId"


# describe-vpc-endpoint-connection-notifications
# describe-vpc-endpoint-connections
# describe-vpc-endpoint-service-configurations


class vpc_endpoint_services(_data_two_deep):
    datatype = "aws.ec2.vpc_endpoint_services"
    operator = "describe_vpc_endpoint_services"
    r1_key = "ServiceDetails"
    r2_id = "ServiceId"


# describe-vpc-endpoints
# describe-vpc-peering-connections


class vpcs(_data_two_deep):
    datatype = "aws.ec2.vpcs"
    operator = "describe_vpcs"
    r1_key = "Vpcs"
    r2_id = "VpcId"


# describe-vpn-connections
# describe-vpn-gateways
