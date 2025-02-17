import aws


_service_name = "billingconductor"
datatype_prefix = "aws." + _service_name + "."


class base(aws.base):
    service_name = _service_name


class account_associations(base, aws._data_two_deep):
    datatype = datatype_prefix + "account_associations"
    operator = "describe_account_associations"
    r1_key = "LinkedAccounts"
    r2_id = "AccountId"
