import aws


class base(aws.base):
    service_name = "eks"


class _cluster_foreach(base):
    def _fetch_one_client(self, client):
        # first, get the list of clusters
        handler = clusters()
        handler.verbose = self.verbose
        names = handler._fetch_one_client(client)

        self._log_fetch_op(client, self.operator)

        data = {}
        for name in names.keys():
            for r1 in self._paged_op(client, self.operator, clusterName=name):
                data[name] = r1[self.r1_key]

        return data


class access_entries(_cluster_foreach):
    datatype = "aws.eks.access_entries"
    operator = "list_access_entries"
    r1_key = "accessEntries"


class addons(_cluster_foreach):
    datatype = "aws.eks.addons"
    operator = "list_addons"
    r1_key = "addons"


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
    operator = "list_nodegroups"
    r1_key = "nodegroups"


class pod_identity_associations(_cluster_foreach):
    datatype = "aws.eks.pod_identity_associations"
    operator = "list_pod_identity_associations"
    r1_key = "associations"


class clusters(base):
    datatype = "aws.eks.clusters"
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
