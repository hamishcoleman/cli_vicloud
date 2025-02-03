import aws


class base(aws.base):
    service_name = "elbv2"


class load_balancers(base, aws._data_two_deep):
    datatype = "aws.elbv2.load_balancers"
    operator = "describe_load_balancers"
    r1_key = "LoadBalancers"
    r2_id = "LoadBalancerName"


class target_groups(base, aws._data_two_deep):
    datatype = "aws.elbv2.target_groups"
    operator = "describe_target_groups"
    r1_key = "TargetGroups"
    r2_id = "TargetGroupName"
