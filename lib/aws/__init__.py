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
                "region": region,
                "session": session,
            }
            sessions.append(this)

    return sessions


class base:
    single_region = False

    def __init__(self):
        self.verbose = 0

    def fetch(self, args, sessions):
        db = definitionset.DefinitionSet()
        profiles_done = {}
        for session in sessions:
            profile_name = session["session"].profile_name
            if self.verbose:
                print(
                    f'{profile_name}:{session["region"]}: fetch',
                    file=sys.stderr
                )

            if self.single_region and profile_name in profiles_done:
                # skip all but the first region
                # TODO: use a cannonical region!
                continue
            profiles_done[profile_name] = True

            resultset = definitionset.Definition()
            resultset.datatype = self.datatype
            resultset.region = session["region"]
            resultset.session = session["session"]

            client = resultset.session.client(
                self.service_name,
                region_name=resultset.region,
            )

            specifics = self._fetch_one_client(client)
            if specifics:
                resultset.data = specifics
                db.append(resultset)

        return db

    def _fetch_one_client(self, client):
        raise NotImplementedError

    def apply(self, data):
        raise NotImplementedError

    @classmethod
    def _paged_op(cls, client, operation):
        """Wrap possible pagination in a helper"""

        if not client.can_paginate(operation):
            operator = getattr(client, operation)
            yield operator()
        else:
            token = None
            paginator = client.get_paginator(operation)

            response = paginator.paginate(
                PaginationConfig={
                    "PageSize": 50,
                    "StartingToken": token,
                }
            )

            for page in response:
                # TODO
                # if not quiet and enough tags since last print
                #   print stderr fetching ...
                yield page


class _data_two_deep(base):
    """Generic parser for simple structure with two layers"""
    def _fetch_one_client(self, client):
        data = {}

        for r1 in self._paged_op(client, self.operator):
            for r2 in r1[self.r1_key]:
                _id = r2[self.r2_id]
                data[_id] = r2

        return data
