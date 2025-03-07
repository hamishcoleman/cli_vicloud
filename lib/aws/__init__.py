import boto3
import botocore
import definitionset
import sys


def setup_sessions(verbose, profiles, regions):
    sessions = []

    if not profiles:
        session = boto3.Session()
        profiles = session.available_profiles

    for profile in profiles:
        session = boto3.Session(profile_name=profile)

        if not regions:
            # Get the list of regions enabled for our profile
            client = session.client("ec2", region_name="ap-southeast-2")
            if verbose:
                print(f"{profile}: describe_regions", file=sys.stderr)

            try:
                reply = client.describe_regions()
                this_regions = [r['RegionName'] for r in reply['Regions']]
            except botocore.exceptions.ClientError:
                print(f"Error fetching regions for {profile}", file=sys.stderr)
                this_regions = []

        else:
            this_regions = regions

        for region in this_regions:
            this = {
                "profile": profile,
                "region": region,
                "session": session,
            }
            sessions.append(this)

    return sessions


class base:
    single_region = False
    dump = False

    def __init__(self):
        self.verbose = 0

    def _log_fetch_op(self, client, operation):
        # Note we are abusing the client object with ou profile name storage
        profile_name = client._profile_name
        region = client._client_config.region_name
        service_name = self.service_name

        if self.verbose:
            print(
                f"{profile_name}:{region}:{service_name} fetch {operation}",
                file=sys.stderr
            )

    def fetch(self, args, sessions):
        db = definitionset.DefinitionSet()
        profiles_done = {}
        for session in sessions:
            profile_name = session["session"].profile_name
            region_name = session["region"]

            if self.single_region:
                region_name = "__SINGLE_REGION"

                if profile_name in profiles_done:
                    # skip all but the first region
                    continue
            profiles_done[profile_name] = True

            resultset = definitionset.Definition()
            resultset.datatype = self.datatype
            resultset.region = region_name
            resultset.session = session["session"]

            client = resultset.session.client(
                self.service_name,
                region_name=session["region"],
            )
            # stash our name inside their client object
            client._profile_name = profile_name

            try:
                specifics = self._fetch_one_client(client, args=args)
            except:
                # TODO: bubble this condition up, mark that profile as
                # possibly skippable
                specifics = None

            if not specifics:
                continue

            self._mutate(specifics)

            resultset.data = specifics
            db.append(resultset)

        return db

    def _mutate(self, data):
        """Optionally mutate data before storing it"""
        return

    def _fetch_one_client(self, client, args=None):
        raise NotImplementedError

    def apply(self, data):
        raise NotImplementedError

    @classmethod
    def _paged_op(cls, client, operation, **kwargs):
        """Wrap possible pagination in a helper"""

        if not client.can_paginate(operation):
            operator = getattr(client, operation)
            yield operator(**kwargs)
        else:
            token = None
            paginator = client.get_paginator(operation)

            param = {
                "PaginationConfig": {
                    "PageSize": 50,
                    "StartingToken": token,
                }
            }
            param.update(kwargs)

            response = paginator.paginate(**param)

            for page in response:
                # TODO
                # if not quiet and enough tags since last print
                #   print stderr fetching ...
                yield page


class _data_two_deep(base):
    """Generic parser for simple structure with two layers"""
    def _fetch_one_client(self, client, args=None):
        data = {}

        self._log_fetch_op(client, self.operator)

        for r1 in self._paged_op(client, self.operator):
            for r2 in r1[self.r1_key]:
                _id = r2[self.r2_id]
                data[_id] = r2

        return data


class _mutate_sortarray(base):
    """Apply any array order stabilisation steps"""

    def _mutate(self, data):
        # Chain to any other mutators
        super()._mutate(data)

        def do_sort(array, orderby):
            def _key(item):
                return item.get(orderby, None)

            return sorted(array, key=_key)

        for _id, item in data.items():
            for keyname, orderby in self.sortarray.items():
                item[keyname] = do_sort(item[keyname], orderby)
