"""Virtual machines (Elastic Compute Cloud)"""
import aws


_service_name = "ec2"
datatype_prefix = "aws." + _service_name + "."


class base(aws.base):
    service_name = _service_name


class account_attributes(base):
    datatype = datatype_prefix + "account_attributes"
    dump = True

    def _fetch_one_client(self, client, args=None):
        data = {}
        operator = "describe_account_attributes"
        r1_key = "AccountAttributes"

        self._log_fetch_op(client, operator)

        for r1 in self._paged_op(client, operator):
            for r2 in r1[r1_key]:
                k = r2["AttributeName"]

                values = []
                for value in r2["AttributeValues"]:
                    values.append(value["AttributeValue"])

                data[k] = ",".join(values)

        return {"0": data}


class availability_zones(base, aws._data_two_deep):
    # TODO
    # This is different per region, but not per account, so can skip
    datatype = datatype_prefix + "availability_zones"
    operator = "describe_availability_zones"
    r1_key = "AvailabilityZones"
    r2_id = "ZoneId"


class dhcp_options(base):
    datatype = datatype_prefix + "dhcp_options"
    dump = True

    def _fetch_one_client(self, client, args=None):
        data = {}
        operator = "describe_dhcp_options"
        r1_key = "DhcpOptions"
        r2_id = "DhcpOptionsId"

        self._log_fetch_op(client, operator)

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


class host_reservation_offerings(base, aws._data_two_deep):
    datatype = datatype_prefix + "host_reservation_offerings"
    operator = "describe_host_reservation_offerings"
    r1_key = "OfferingSet"
    r2_id = "OfferingId"


class images(base, aws._data_two_deep):
    datatype = datatype_prefix + "images"
    operator = "describe_images"
    r1_key = "Images"
    r2_id = "ImageId"


class instance_credit_specifications(base, aws._data_two_deep):
    datatype = datatype_prefix + "instance_credit_specifications"
    operator = "describe_instance_credit_specifications"
    r1_key = "InstanceCreditSpecifications"
    r2_id = "InstanceId"


class instance_types(base, aws._data_two_deep):
    datatype = datatype_prefix + "instance_types"
    operator = "describe_instance_types"
    r1_key = "InstanceTypes"
    r2_id = "InstanceType"


class instances(base):
    datatype = datatype_prefix + "instances"
    dump = True

    def _fetch_one_client(self, client, args=None):
        data = {}
        operator = "describe_instances"
        r1_key = "Reservations"
        r2_key = "Instances"
        r3_id = "InstanceId"

        self._log_fetch_op(client, operator)

        for r1 in self._paged_op(client, operator):
            for r2 in r1[r1_key]:
                for r3 in r2[r2_key]:
                    _id = r3[r3_id]
                    data[_id] = r3

        return data


class internet_gateways(base, aws._data_two_deep):
    datatype = datatype_prefix + "internet_gateways"
    dump = True
    operator = "describe_internet_gateways"
    r1_key = "InternetGateways"
    r2_id = "InternetGatewayId"


class key_pairs(base, aws._data_two_deep):
    datatype = datatype_prefix + "key_pairs"
    dump = True
    operator = "describe_key_pairs"
    r1_key = "KeyPairs"
    r2_id = "KeyPairId"


class launch_template_versions(base):
    """Fetch the most recent version of each template"""
    datatype = datatype_prefix + "launch_template_versions"
    dump = True
    operator = "describe_launch_template_versions"
    r1_key = "LaunchTemplateVersions"
    r2_id = "LaunchTemplateId"

    def _fetch_one_client(self, client, args=None):
        data = {}

        self._log_fetch_op(client, self.operator)

        for r1 in self._paged_op(client, self.operator, Versions=["$Latest"]):
            for r2 in r1[self.r1_key]:
                _id = r2[self.r2_id]
                data[_id] = r2

        return data


class launch_templates(base, aws._data_two_deep):
    datatype = datatype_prefix + "launch_templates"
    dump = True
    operator = "describe_launch_templates"
    r1_key = "LaunchTemplates"
    r2_id = "LaunchTemplateId"


class managed_prefix_lists(base, aws._data_two_deep):
    datatype = datatype_prefix + "managed_prefix_lists"
    operator = "describe_managed_prefix_lists"
    r1_key = "PrefixLists"
    r2_id = "PrefixListId"


# describe-nat-gateways
# describe-network-acls
# describe-network-interface-permissions


class network_interfaces(base, aws._data_two_deep):
    datatype = datatype_prefix + "network_interfaces"
    dump = True
    operator = "describe_network_interfaces"
    r1_key = "NetworkInterfaces"
    r2_id = "NetworkInterfaceId"


class prefix_lists(base, aws._data_two_deep):
    datatype = datatype_prefix + "prefix_lists"
    operator = "describe_prefix_lists"
    r1_key = "PrefixLists"
    r2_id = "PrefixListId"


class regions(base, aws._data_two_deep):
    datatype = datatype_prefix + "regions"
    operator = "describe_regions"
    single_region = True
    r1_key = "Regions"
    r2_id = "RegionName"


class route_tables(base, aws._data_two_deep, aws._mutate_sortarray):
    datatype = datatype_prefix + "route_tables"
    dump = True
    operator = "describe_route_tables"
    r1_key = "RouteTables"
    r2_id = "RouteTableId"
    sortarray = {
        "Associations": "RouteTableAssociationId",
    }


class security_group_rules(base, aws._data_two_deep):
    datatype = datatype_prefix + "security_group_rules"
    dump = True
    operator = "describe_security_group_rules"
    r1_key = "SecurityGroupRules"
    r2_id = "SecurityGroupRuleId"


class snapshots(base, aws._data_two_deep):
    datatype = datatype_prefix + "snapshots"
    operator = "describe_snapshots"
    r1_key = "Snapshots"
    r2_id = "SnapshotId"


class subnets(base, aws._data_two_deep):
    datatype = datatype_prefix + "subnets"
    dump = True
    operator = "describe_subnets"
    r1_key = "Subnets"
    r2_id = "SubnetId"


class tags(base):
    """Edit ec2 tags"""
    datatype = datatype_prefix + "tags"
    dump = True

    def _fetch_one_client(self, client, args=None):
        data = {}
        operator = "describe_tags"
        r1_key = "Tags"
        r2_id = "ResourceId"

        self._log_fetch_op(client, operator)

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


class volume_status(base, aws._data_two_deep):
    datatype = datatype_prefix + "volume_status"
    dump = True
    operator = "describe_volume_status"
    r1_key = "VolumeStatuses"
    r2_id = "VolumeId"


class volumes(base, aws._data_two_deep):
    datatype = datatype_prefix + "volumes"
    dump = True
    operator = "describe_volumes"
    r1_key = "Volumes"
    r2_id = "VolumeId"


# describe-vpc-endpoint-connection-notifications
# describe-vpc-endpoint-connections
# describe-vpc-endpoint-service-configurations


class vpc_endpoint_services(base, aws._data_two_deep):
    datatype = datatype_prefix + "vpc_endpoint_services"
    operator = "describe_vpc_endpoint_services"
    r1_key = "ServiceDetails"
    r2_id = "ServiceId"


# describe-vpc-endpoints
# describe-vpc-peering-connections


class vpcs(base, aws._data_two_deep):
    datatype = datatype_prefix + "vpcs"
    dump = True
    operator = "describe_vpcs"
    r1_key = "Vpcs"
    r2_id = "VpcId"


# describe-vpn-connections
# describe-vpn-gateways
