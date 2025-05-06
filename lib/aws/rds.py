"""RDS"""
import aws


_service_name = "rds"
datatype_prefix = "aws." + _service_name + "."


class base(aws.base):
    service_name = _service_name


class db_clusters(base, aws._data_two_deep):
    datatype = datatype_prefix + "db_clusters"
    operator = "describe_db_clusters"
    r1_key = "DBClusters"
    r2_id = "DBClusterIdentifier"

