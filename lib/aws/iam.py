import aws


class base(aws.base):
    service_name = "iam"


class list_users(base, aws._data_two_deep):
    datatype = "aws.iam.list_users"
    operator = "list_users"
    single_region = True
    r1_key = "Users"
    r2_id = "UserId"
