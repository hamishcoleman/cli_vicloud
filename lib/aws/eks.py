import aws


class base(aws.base):
    service_name = "eks"


class _cluster_foreach(base):
    cluster_param_name = "clusterName"

    def _fetch_one_client(self, client):
        # first, get the list of clusters
        handler = list_clusters()
        handler.verbose = self.verbose
        names = handler._fetch_one_client(client)

        self._log_fetch_op(client, self.operator)

        data = {}
        for name in names.keys():
            kwargs = {
                self.cluster_param_name: name,
            }
            for r1 in self._paged_op(client, self.operator, **kwargs):
                data[name] = r1[self.r1_key]

        return data


class access_entries(base):
    datatype = "aws.eks.access_entry"
    dump = True
    operator = "describe_access_entry"
    r1_key = "accessEntry"
    r2_id = "accessEntryArn"

    def _fetch_one_client(self, client):
        # first, get the list of clusters
        handler = list_clusters()
        handler.verbose = self.verbose
        clusters = handler._fetch_one_client(client)

        for cluster in clusters.keys():
            handler = list_access_entries()
            handler.verbose = self.verbose
            access_entries = handler._fetch_one_client(client)

            self._log_fetch_op(client, self.operator)

            data = {}
            for access in access_entries[cluster]:
                kwargs = {
                    "clusterName": cluster,
                    "principalArn": access,
                }
                for r1 in self._paged_op(client, self.operator, **kwargs):
                    _id = r1[self.r1_key][self.r2_id]
                    data[_id] = r1[self.r1_key]

        return data


class addons(_cluster_foreach):
    datatype = "aws.eks.addons"
    dump = True
    operator = "list_addons"
    r1_key = "addons"


class cluster(_cluster_foreach):
    datatype = "aws.eks.cluster"
    dump = True
    operator = "describe_cluster"
    r1_key = "cluster"
    cluster_param_name = "name"



class fargate_profiles(_cluster_foreach):
    datatype = "aws.eks.fargate_profiles"
    operator = "list_fargate_profiles"
    r1_key = "fargateProfileNames"


# class identity_provider_configs(_cluster_foreach):
#     datatype = "aws.eks.identity_provider_configs"
#     operator = "list_identity_provider_configs"
#     r1_key = "fargateProfileNames"
#
# botocore.errorfactory.InvalidParameterException:
# An error occurred (InvalidParameterException) when calling the
# ListIdentityProviderConfigs operation: maxResults needs to be 1


class insights(_cluster_foreach):
    datatype = "aws.eks.insights"
    operator = "list_insights"
    r1_key = "insights"


class nodegroups(_cluster_foreach):
    datatype = "aws.eks.nodegroups"
    dump = True
    operator = "list_nodegroups"
    r1_key = "nodegroups"


class pod_identity_associations(_cluster_foreach):
    datatype = "aws.eks.pod_identity_associations"
    dump = True
    operator = "list_pod_identity_associations"
    r1_key = "associations"


class list_access_entries(_cluster_foreach):
    operator = "list_access_entries"
    r1_key = "accessEntries"


class list_clusters(base):
    operator = "list_clusters"
    r1_key = "clusters"

    def _fetch_one_client(self, client):
        data = {}

        self._log_fetch_op(client, self.operator)

        for r1 in self._paged_op(client, self.operator):
            for r2 in r1[self.r1_key]:
                data[r2] = {
                    "_exists": True,
                }

        return data
