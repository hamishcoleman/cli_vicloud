"""The Amazon DNS service"""
import aws


_service_name = "route53"
datatype_prefix = "aws." + _service_name + "."


class base(aws.base):
    service_name = _service_name


class hosted_zones(base, aws._data_two_deep):
    datatype = datatype_prefix + "hosted_zones"
    dump = True
    operator = "list_hosted_zones"
    r1_key = "HostedZones"
    r2_id = "Name"


class resource_record_sets(base):
    datatype = datatype_prefix + "resource_record_sets"
    dump = True
    operator = "list_resource_record_sets"
    r1_key = "ResourceRecordSets"

    def _fetch_one_client(self, client, args=None):
        # first, get the list of clusters
        handler = hosted_zones()
        handler.verbose = self.verbose
        zones = handler._fetch_one_client(client)

        data = {}
        for zone in zones.values():
            kwargs = {
                "HostedZoneId": zone["Id"],
            }

            self._log_fetch_op(client, self.operator)
            for r1 in self._paged_op(client, self.operator, **kwargs):
                for record in r1[self.r1_key]:
                    # TODO:
                    # I dont think there are dupes, sicne the Name is a fqdn,
                    # but maybe with a split horizon? could prefix _id with
                    # an id from the zone

                    parts = record["Name"].split(".")
                    if not parts[-1]:
                        # Remove the null caused by the "." terminator
                        del parts[-1]

                    parts.reverse()
                    _id = ".".join(parts) + "/" + record["Type"]

                    data[_id] = record

        return data
