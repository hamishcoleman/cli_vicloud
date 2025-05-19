import boto3
import botocore
import definitionset
import sys
import vicloud


class DataSource(vicloud.DataSource):
    def __init__(self, profile, region):
        self.datatype_prefix = "aws."
        self.profile = profile
        self.region = region
        self.single_region = False
        self._session = None

    def metadata(self):
        meta = {
            "profile": self.profile,
            "region": self.region,
        }
        if self.single_region:
            meta["single_region"] = True
        return meta

    @property
    def session(self):
        if self._session is None:
            self._session = boto3.Session(profile_name=self.profile)
        return self._session

    def client(self, service_name):
        region = self.region
        if region == "__SINGLE_REGION":
            # TODO: is there a region name string that AWS uses for this?
            # A random region, chosen by a fair roll of the dice
            region = "ap-southeast-2"
            self.single_region = True

        return self.session.client(
            service_name,
            region_name=region,
        )

    def operation(self, service_name, operation, **kwargs):
        """Wrap possible pagination in a helper"""
        client = self.client(service_name)

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

            # TODO: use a common logger (see base.log())
            if verbose:
                print(f"{profile}: describe_regions", file=sys.stderr)

            try:
                reply = client.describe_regions()
                this_regions = [r['RegionName'] for r in reply['Regions']]
            except botocore.exceptions.ClientError as e:
                code = e.response["Error"]["Code"]
                # TODO: use a common logger (see base.log())
                print(f"{profile}: ERROR: {code}, skipping", file=sys.stderr)
                this_regions = []

        else:
            this_regions = regions

        for region in this_regions:
            this = {
                "enable": True,
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

    def log(self, datasource, message):
        profile = datasource.profile
        region = datasource.region
        if self.verbose:
            print(
                f"{profile}:{region}:{self.service_name} {message}",
                file=sys.stderr
            )

    def log_operator(self, datasource, operation):
        self.log(datasource, f"fetch {operation}")

    def fetch(self, args, sessions):
        db = definitionset.DefinitionSet()
        profiles_done = {}
        for session in sessions:
            if not session["enable"]:
                # Skip sessions that have become error disabled
                continue

            profile_name = session["session"].profile_name
            region_name = session["region"]

            if self.single_region:
                # If this is a global resource, override the region name
                # TODO: is there a region name string that AWS uses for this?
                region_name = "__SINGLE_REGION"

                if profile_name in profiles_done:
                    # skip all but the first region
                    continue
            profiles_done[profile_name] = True

            datasource = DataSource(profile_name, region_name)

            resultset = definitionset.Definition()
            resultset.datasource = datasource
            resultset.datatype = self.datatype

            client = datasource.client(self.service_name)

            # stash our datasource to simplify the transition period
            client._datasource = datasource

            try:
                specifics = self._fetch_one_client(client, args=args)
            except botocore.exceptions.ClientError as e:
                skip_codes = [
                    "AuthFailure",
                    "InvalidClientTokenId",
                    "UnsupportedOperation",
                ]
                code = e.response["Error"]["Code"]

                if code in skip_codes:
                    self.log(datasource, f"ERROR: {code}, skipping")
                    specifics = None

                    # Skip this region for the rest of this run
                    session["enable"] = False
                else:
                    raise
            except botocore.exceptions.TokenRetrievalError:
                # Attempt to provide a better error-message experience
                raise ValueError("TokenRetrievalError: probably not logged in")

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
        datasource = client._datasource
        data = {}

        self.log_operator(datasource, self.operator)

        for r1 in datasource.operation(self.service_name, self.operator):
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


class _mutate_sortTagsarray(base):
    """Apply stabilise the order of the Tags array"""

    def _mutate(self, data):
        # Chain to any other mutators
        super()._mutate(data)

        for _id, item in data.items():
            if "Tags" not in item:
                continue

            tags = {}
            for tag in item["Tags"]:
                k = tag["Key"]
                v = tag["Value"]
                tags[k] = v

            tagarray = []
            for k in sorted(tags.keys()):
                v = tags[k]
                tag = {
                    "Key": k,
                    "Value": v,
                }
                tagarray.append(tag)

            item["Tags"] = tagarray
