import aws


class base(aws.base):
    service_name = "elbv2"


class listeners(base):
    datatype = "aws.elbv2.listeners"

    def _fetch_one_client(self, client):
        # first, get the list of load_balancers
        handler = load_balancers()
        handler.verbose = self.verbose
        loadbalancers = handler._fetch_one_client(client)

        arns = set()
        for _id, elb in loadbalancers.items():
            arns.add(elb["LoadBalancerArn"])

        r1_key = "Listeners"
        r2_id = "ListenerArn"

        data = {}
        for arn in arns:
            for r1 in self._paged_op(
                    client,
                    "describe_listeners",
                    LoadBalancerArn=arn
            ):
                for r2 in r1[r1_key]:
                    _id = r2[r2_id]
                    data[_id] = r2

        return data


class load_balancers(base, aws._data_two_deep):
    datatype = "aws.elbv2.load_balancers"
    operator = "describe_load_balancers"
    r1_key = "LoadBalancers"
    r2_id = "LoadBalancerName"


class rules(base):
    datatype = "aws.elbv2.rules"

    def _fetch_one_client(self, client):
        # first, get the list of listeners
        handler = listeners()
        handler.verbose = self.verbose
        _list = handler._fetch_one_client(client)

        arns = set()
        for _id, listener in _list.items():
            arns.add(listener["ListenerArn"])

        r1_key = "Rules"
        r2_id = "RuleArn"

        data = {}
        for arn in arns:
            for r1 in self._paged_op(
                    client,
                    "describe_rules",
                    ListenerArn=arn
            ):
                for r2 in r1[r1_key]:
                    _id = r2[r2_id]
                    data[_id] = r2

        return data


class target_groups(base, aws._data_two_deep):
    datatype = "aws.elbv2.target_groups"
    operator = "describe_target_groups"
    r1_key = "TargetGroups"
    r2_id = "TargetGroupName"
