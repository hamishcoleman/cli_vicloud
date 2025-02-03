import aws


class base(aws.base):
    service_name = "eks"


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
