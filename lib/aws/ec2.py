import boto3
import definitionset


def setup_sessions(profiles, regions):
    sessions = []

    if not profiles:
        profiles = [None]

    for profile in profiles:
        session = boto3.Session(profile_name=profile)

        if not regions:
            # Get the list of regions enabled for our profile
            client = session.client("ec2", region_name="us-west-2")
            reply = client.describe_regions()
            this_regions = [r['RegionName'] for r in reply['Regions']]
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
    def fetch(self, args, sessions):
        db = definitionset.DefinitionSet()
        for session in sessions:
            # TODO
            # if not quiet
            #  print stderr profile/region

            resultset = definitionset.Definition()
            resultset.datatype = self.datatype
            resultset.region = session["region"]
            resultset.session = session["session"]

            client = resultset.session.client(
                "ec2",
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
    def _paginator_helper(cls, client, operation):
        """Wrap pagination details in a helper"""

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


class tags_handler(base):
    """Edit ec2 tags"""
    datatype = "aws.ec2.tags"

    def _fetch_one_client(self, client):
        specifics = {}
        for page in self._paginator_helper(client, "describe_tags"):
            tags = page["Tags"]
            for tag in tags:
                _id = tag["ResourceId"]
                k = tag["Key"]
                v = tag["Value"]

                if _id not in specifics:
                    specifics[_id] = {}

                specifics[_id][k] = v

        return specifics


class instances_handler(base):
    datatype = "aws.ec2.instances"

    def _fetch_one_client(self, client):
        specifics = {}
        for page in self._paginator_helper(client, "describe_instances"):
            reservations = page["Reservations"]
            for reservation in reservations:
                instances = reservation["Instances"]
                for instance in instances:
                    _id = instance["InstanceId"]
                    specifics[_id] = instance

        return specifics
