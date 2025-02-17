import aws


class base(aws.base):
    service_name = "logs"


class events(base):
    datatype = "aws.logs.events"
    operator = "get_log_events"
    params = ['log_group_name', 'log_stream_name']
    r1_key = "events"

    def _fetch_one_client(self, client, args=None):
        data = {}

        self._log_fetch_op(client, self.operator)

        _id = 0
        for r1 in self._paged_op(client, self.operator, logGroupName=args.log_group_name, logStreamName=args.log_stream_name):
            for r2 in r1[self.r1_key]:
                data[_id] = r2
                _id += 1

        return data


class groups(base, aws._data_two_deep):
    datatype = "aws.logs.groups"
    operator = "describe_log_groups"
    r1_key = "logGroups"
    r2_id = "logGroupName"


class streams(base):
    datatype = "aws.logs.streams"
    operator = "describe_log_streams"
    params = ['log_group_name']
    r1_key = "logStreams"
    r2_id = "logStreamName"

    def _fetch_one_client(self, client, args=None):
        data = {}

        self._log_fetch_op(client, self.operator)

        for r1 in self._paged_op(client, self.operator, logGroupName=args.log_group_name):
            for r2 in r1[self.r1_key]:
                _id = r2[self.r2_id]
                data[_id] = r2

        return data
