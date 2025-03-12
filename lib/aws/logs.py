import aws
import datetime


_service_name = "logs"
datatype_prefix = "aws." + _service_name + "."


class base(aws.base):
    service_name = _service_name


class events(base):
    datatype = datatype_prefix + "events"
    operator = "get_log_events"
    params = ['log_group_name', 'log_stream_name']
    r1_key = "events"

    def _fetch_one_client(self, client, args=None):
        datasource = client._datasource
        data = {}

        self.log_operator(datasource, self.operator)

        _id = 0
        for r1 in self._paged_op(
                client,
                self.operator,
                logGroupName=args.log_group_name,
                logStreamName=args.log_stream_name
        ):
            for r2 in r1[self.r1_key]:
                data[_id] = r2
                _id += 1

        return data


class groups(base, aws._data_two_deep):
    datatype = datatype_prefix + "groups"
    operator = "describe_log_groups"
    r1_key = "logGroups"
    r2_id = "logGroupName"


class streams(base):
    datatype = datatype_prefix + "streams"
    operator = "describe_log_streams"
    params = ['log_group_name']
    r1_key = "logStreams"
    r2_id = "logStreamName"

    def _fetch_one_client(self, client, args=None):
        datasource = client._datasource
        data = {}

        self.log_operator(datasource, self.operator)

        for r1 in self._paged_op(
                client,
                self.operator,
                logGroupName=args.log_group_name
        ):
            for r2 in r1[self.r1_key]:
                _id = r2[self.r2_id]
                data[_id] = r2

        return data

    def _mutate(self, data):
        # Chain to any other mutators
        super()._mutate(data)

        timefields = [
            "creationTime",
            "firstEventTimestamp",
            "lastEventTimestamp",
            "lastIngestionTime",
        ]

        for _id, item in data.items():
            for i in timefields:
                if i in item:
                    timestamp = item[i] / 1000
                    dt = datetime.datetime.fromtimestamp(
                        timestamp,
                        tz=datetime.timezone.utc
                    ).astimezone()
                    item[i] = dt.isoformat(timespec="milliseconds")
