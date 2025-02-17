import aws


class base(aws.base):
    service_name = "elbv2"


class listeners(base):
    datatype = "aws.elbv2.listeners"
    dump = True

    def _fetch_one_client(self, client, args=None):
        # first, get the list of load_balancers
        handler = load_balancers()
        handler.verbose = self.verbose
        loadbalancers = handler._fetch_one_client(client)

        arns = set()
        for _id, elb in loadbalancers.items():
            arns.add(elb["LoadBalancerArn"])

        operator = "describe_listeners"
        r1_key = "Listeners"
        r2_id = "ListenerArn"

        self._log_fetch_op(client, operator)

        data = {}
        for arn in arns:
            for r1 in self._paged_op(client, operator, LoadBalancerArn=arn):
                for r2 in r1[r1_key]:
                    _id = r2[r2_id]
                    data[_id] = r2

        return data


class load_balancers(base, aws._data_two_deep):
    datatype = "aws.elbv2.load_balancers"
    dump = True
    operator = "describe_load_balancers"
    r1_key = "LoadBalancers"
    r2_id = "LoadBalancerName"


class rules(base):
    datatype = "aws.elbv2.rules"
    dump = True

    def _fetch_one_client(self, client, args=None):
        # first, get the list of listeners
        handler = listeners()
        handler.verbose = self.verbose
        _list = handler._fetch_one_client(client)

        arns = set()
        for _id, listener in _list.items():
            arns.add(listener["ListenerArn"])

        operator = "describe_rules"
        r1_key = "Rules"
        r2_id = "RuleArn"

        self._log_fetch_op(client, operator)

        data = {}
        for arn in arns:
            for r1 in self._paged_op(client, operator, ListenerArn=arn):
                for r2 in r1[r1_key]:
                    _id = r2[r2_id]
                    data[_id] = r2

        return data


class target_groups(base, aws._data_two_deep):
    datatype = "aws.elbv2.target_groups"
    dump = True
    operator = "describe_target_groups"
    r1_key = "TargetGroups"
    r2_id = "TargetGroupName"
