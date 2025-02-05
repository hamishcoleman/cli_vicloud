import aws


class base(aws.base):
    service_name = "billingconductor"


class account_associations(base, aws._data_two_deep):
    datatype = "aws.billingconductor.account_associations"
    operator = "describe_account_associations"
    r1_key = "LinkedAccounts"
    r2_id = "AccountId"
