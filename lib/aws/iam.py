import aws


class base(aws.base):
    service_name = "iam"


class list_users(base, aws._data_two_deep):
    datatype = "aws.iam.list_users"
    # Note: dumping a single_region object may cause non idempotent regions
    dump = True
    operator = "list_users"
    single_region = True
    r1_key = "Users"
    r2_id = "UserId"


class list_roles(base, aws._data_two_deep):
    datatype = "aws.iam.list_roles"
    operator = "list_roles"
    single_region = True
    r1_key = "Roles"
    r2_id = "RoleId"
