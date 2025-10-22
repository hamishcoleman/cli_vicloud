"""Elastic Load Balancer"""
import aws


_service_name = "elbv2"
datatype_prefix = "aws." + _service_name + "."


class base(aws.base):
    service_name = _service_name


class listener_attributes(base):
    datatype = datatype_prefix + "listener_attributes"
    dump = True

    def _fetch_one_client(self, client, args=None):
        datasource = client._datasource
        # first, get the list of load_balancers
        handler = listeners()
        handler.verbose = self.verbose
        listenlist = handler._fetch_one_client(client)

        arns = set()
        for _id, listener in listenlist.items():
            arns.add(listener["ListenerArn"])

        operator = "describe_listener_attributes"
        r1_key = "Attributes"

        self.log_operator(datasource, operator)

        data = {}
        for arn in arns:
            data[arn] = {}
            for r1 in self._paged_op(client, operator, ListenerArn=arn):
                for attrib in r1[r1_key]:
                    k = attrib["Key"]
                    v = attrib["Value"]

                    data[arn][k] = v

        return data


class listener_certificates(base):
    datatype = datatype_prefix + "listener_certificates"
    dump = True

    def _fetch_one_client(self, client, args=None):
        datasource = client._datasource
        # first, get the list of load_balancers
        handler = listeners()
        handler.verbose = self.verbose
        listenlist = handler._fetch_one_client(client)

        arns = set()
        for _id, listener in listenlist.items():
            arns.add(listener["ListenerArn"])

        operator = "describe_listener_certificates"
        r1_key = "Certificates"

        self.log_operator(datasource, operator)

        data = {}
        for arn in arns:
            data[arn] = []
            for r1 in self._paged_op(client, operator, ListenerArn=arn):
                # It eppears that some items just dont have data, so skip them
                if r1_key in r1:
                    data[arn] += r1[r1_key]

        return data


class listeners(base):
    datatype = datatype_prefix + "listeners"
    dump = True

    def _fetch_one_client(self, client, args=None):
        datasource = client._datasource
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

        self.log_operator(datasource, operator)

        data = {}
        for arn in arns:
            for r1 in self._paged_op(client, operator, LoadBalancerArn=arn):
                for r2 in r1[r1_key]:
                    _id = r2[r2_id]
                    data[_id] = r2

        return data


class load_balancer_attributes(base):
    datatype = datatype_prefix + "load_balancer_attributes"
    dump = True

    def _fetch_one_client(self, client, args=None):
        datasource = client._datasource
        # first, get the list of load_balancers
        handler = load_balancers()
        handler.verbose = self.verbose
        loadbalancers = handler._fetch_one_client(client)

        arns = set()
        for _id, elb in loadbalancers.items():
            arns.add(elb["LoadBalancerArn"])

        operator = "describe_load_balancer_attributes"
        r1_key = "Attributes"

        self.log_operator(datasource, operator)

        data = {}
        for arn in arns:
            data[arn] = {}
            for r1 in self._paged_op(client, operator, LoadBalancerArn=arn):
                for attrib in r1[r1_key]:
                    k = attrib["Key"]
                    v = attrib["Value"]

                    data[arn][k] = v

        return data


class load_balancers(base, aws._data_two_deep):
    datatype = datatype_prefix + "load_balancers"
    dump = True
    operator = "describe_load_balancers"
    r1_key = "LoadBalancers"
    r2_id = "LoadBalancerName"


class rules(base):
    datatype = datatype_prefix + "rules"
    dump = True

    def _fetch_one_client(self, client, args=None):
        datasource = client._datasource
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

        self.log_operator(datasource, operator)

        data = {}
        for arn in arns:
            for r1 in self._paged_op(client, operator, ListenerArn=arn):
                for r2 in r1[r1_key]:
                    _id = r2[r2_id]
                    data[_id] = r2

        return data


class target_groups(base, aws._data_two_deep):
    datatype = datatype_prefix + "target_groups"
    dump = True
    operator = "describe_target_groups"
    r1_key = "TargetGroups"
    r2_id = "TargetGroupName"


class target_group_attributes(base):
    datatype = datatype_prefix + "target_group_attributes"
    dump = True

    def _fetch_one_client(self, client, args=None):
        datasource = client._datasource
        # first, get the list of target_groups
        handler = target_groups()
        handler.verbose = self.verbose
        listgroups = handler._fetch_one_client(client)

        arns = set()
        for _id, item in listgroups.items():
            arns.add(item["TargetGroupArn"])

        operator = "describe_target_group_attributes"
        r1_key = "Attributes"

        self.log_operator(datasource, operator)

        data = {}
        for arn in arns:
            data[arn] = {}
            for r1 in self._paged_op(client, operator, TargetGroupArn=arn):
                for attrib in r1[r1_key]:
                    k = attrib["Key"]
                    v = attrib["Value"]

                    data[arn][k] = v

        return data


class target_health(base):
    datatype = datatype_prefix + "target_health"
    dump = True

    def _fetch_one_client(self, client, args=None):
        datasource = client._datasource
        # first, get the list of target_groups
        handler = target_groups()
        handler.verbose = self.verbose
        listgroups = handler._fetch_one_client(client)

        arns = set()
        for _id, item in listgroups.items():
            arns.add(item["TargetGroupArn"])

        operator = "describe_target_health"
        r1_key = "TargetHealthDescriptions"

        self.log_operator(datasource, operator)

        data = {}
        for arn in arns:
            data[arn] = {
                "_arn": arn,
                "TargetHealthDescriptions": {},
            }
            for r1 in self._paged_op(client, operator, TargetGroupArn=arn):
                for health in r1[r1_key]:
                    _id = f'{health["Target"]["Id"]}/{health["Target"]["Port"]}'

                    # This key provides the current status, not the config
                    # TODO: optionally expose this
                    del health["TargetHealth"]

                    data[arn]["TargetHealthDescriptions"][_id] = health

        return data
