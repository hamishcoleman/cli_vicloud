import aws


_service_name = "ssm"
datatype_prefix = "aws." + _service_name + "."


class base(aws.base):
    service_name = _service_name


class parameters(base):
    datatype = datatype_prefix + "parameters"
    operator = "get_parameters_by_path"
    params = ['--path', '--recursive']
    r1_key = "Parameters"

    def _fetch_one_client(self, client, args=None):
        datasource = client._datasource
        data = {}

        # Default to listing the list of params
        if args.path is None:
            args.path = "/aws/service/list"

        self.log_operator(datasource, self.operator)

        param = {
            "PaginationConfig": {
                "PageSize": 10,
            },
            "Path": args.path,
        }

        if args.recursive == "true":
            param["Recursive"] = True

        _id = 0
        for r1 in self._paged_op(client, self.operator, **param):
            for r2 in r1[self.r1_key]:
                data[_id] = r2
                _id += 1

        return data
