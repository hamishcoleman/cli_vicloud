"""RDS"""
import aws


_service_name = "rds"
datatype_prefix = "aws." + _service_name + "."


class base(aws.base):
    service_name = _service_name


class certificate(base, aws._data_two_deep):
    datatype = datatype_prefix + "certificate"
    dump = True
    operator = "describe_certificates"
    r1_key = "Certificates"
    r2_id = "CertificateIdentifier"


class db_cluster_automated_backup(base, aws._data_two_deep):
    datatype = datatype_prefix + "db_cluster_automated_backup"
    dump = True
    operator = "describe_db_cluster_automated_backups"
    r1_key = "DBClusterAutomatedBackups"
    r2_id = "DBClusterIdentifier"


class db_cluster_endpoint(base, aws._data_two_deep):
    datatype = datatype_prefix + "db_cluster_endpoint"
    dump = True
    operator = "describe_db_cluster_endpoints"
    r1_key = "DBClusterEndpoints"
    r2_id = "Endpoint"


class db_cluster_parameter_group(base, aws._data_two_deep):
    datatype = datatype_prefix + "db_cluster_parameter_group"
    dump = True
    operator = "describe_db_cluster_parameter_groups"
    r1_key = "DBClusterParameterGroups"
    r2_id = "DBClusterParameterGroupName"


class db_cluster_parameter(base):
    datatype = datatype_prefix + "db_cluster_parameter"
    dump = True

    def _fetch_one_client(self, client, args=None):
        datasource = client._datasource
        # first, get the list of listeners
        handler = db_cluster_parameter_group()
        handler.verbose = self.verbose
        _list = handler._fetch_one_client(client)

        groups = set()
        for _id in _list.keys():
            groups.add(_id)

        operator = "describe_db_cluster_parameters"
        r1_key = "Parameters"
        r2_id = "ParameterName"

        self.log_operator(datasource, operator)

        data = {}
        for group in groups:
            for r1 in self._paged_op(
                    client,
                    operator,
                    DBClusterParameterGroupName=group
            ):
                for r2 in r1[r1_key]:
                    _id = ".".join([group, r2[r2_id]])
                    data[_id] = r2

        return data


class db_cluster_snapshot(base, aws._data_two_deep):
    datatype = datatype_prefix + "db_cluster_snapshot"
    dump = True
    operator = "describe_db_cluster_snapshots"
    r1_key = "DBClusterSnapshots"
    r2_id = "DBClusterSnapshotIdentifier"


class db_cluster(base, aws._data_two_deep):
    datatype = datatype_prefix + "db_cluster"
    dump = True
    operator = "describe_db_clusters"
    r1_key = "DBClusters"
    r2_id = "DBClusterIdentifier"


class db_engine_version(base, aws._data_two_deep):
    datatype = datatype_prefix + "db_engine_version"
    dump = False
    operator = "describe_db_engine_versions"
    r1_key = "DBEngineVersions"

    def _fetch_one_client(self, client, args=None):
        self.log_operator(client._datasource, self.operator)

        data = {}
        for r1 in self._paged_op(client, self.operator):
            for r2 in r1[self.r1_key]:
                _id = ".".join([r2["Engine"], r2["EngineVersion"]])
                data[_id] = r2

        return data


class db_instance_automated_backup(base, aws._data_two_deep):
    datatype = datatype_prefix + "db_instance_automated_backup"
    dump = True
    operator = "describe_db_instance_automated_backups"
    r1_key = "DBInstanceAutomatedBackups"
    r2_id = "DbiResourceId"


class db_instance(base, aws._data_two_deep):
    datatype = datatype_prefix + "db_instance"
    dump = True
    operator = "describe_db_instances"
    r1_key = "DBInstances"
    r2_id = "DBInstanceIdentifier"


class db_log_file(base):
    datatype = datatype_prefix + "db_log_file"
    dump = False

    def _fetch_one_client(self, client, args=None):
        datasource = client._datasource
        # first, get the list of listeners
        handler = db_instance()
        handler.verbose = self.verbose
        _list = handler._fetch_one_client(client)

        instances = set()
        for _id in _list.keys():
            instances.add(_id)

        operator = "describe_db_log_files"
        r1_key = "DescribeDBLogFiles"
        r2_id = "LogFileName"

        self.log_operator(datasource, operator)

        data = {}
        for instance in instances:
            for r1 in self._paged_op(
                    client,
                    operator,
                    DBInstanceIdentifier=instance
            ):
                for r2 in r1[r1_key]:
                    _id = "/".join([instance, r2[r2_id]])
                    data[_id] = r2

        return data
