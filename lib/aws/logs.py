import aws


class base(aws.base):
    service_name = "logs"


class log_groups(base, aws._data_two_deep):
    datatype = "aws.logs.log_groups"
    operator = "describe_log_groups"
    r1_key = "logGroups"
    r2_id = "logGroupName"



