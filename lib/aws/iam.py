import aws


class base(aws.base):
    service_name = "iam"


class list_access_keys(base):
    datatype = "aws.iam.access_keys"
    dump = True
    operator = "list_access_keys"
    single_region = True
    r1_key = "AccessKeyMetadata"
    r3_id = "AccessKeyId"

    def _fetch_one_client(self, client):
        # first, get the list of users
        handler = list_users()
        handler.verbose = self.verbose
        users = handler._fetch_one_client(client)

        data = {}
        for _id, user in users.items():
            self._log_fetch_op(client, self.operator)

            kwargs = {
                "UserName": user["UserName"],
            }
            for r1 in self._paged_op(client, self.operator, **kwargs):
                r2 = r1[self.r1_key]
                for r3 in r2:
                    _id = r3[self.r3_id]
                    data[_id] = r3

        return data


# list-account-aliases
# list-attached-group-policies GroupName
# list-attached-role-policies RoleName


class list_attached_user_policies(base):
    datatype = "aws.iam.attached_user_policies"
    dump = True
    operator = "list_attached_user_policies"
    single_region = True
    r1_key = "AttachedPolicies"

    def _fetch_one_client(self, client):
        # first, get the list of users
        handler = list_users()
        handler.verbose = self.verbose
        users = handler._fetch_one_client(client)

        data = {}
        for _id, user in users.items():
            self._log_fetch_op(client, self.operator)

            username = user["UserName"]
            kwargs = {
                "UserName": username,
            }
            for r1 in self._paged_op(client, self.operator, **kwargs):
                del r1["ResponseMetadata"]
                del r1["IsTruncated"]
                r1["_UserName"] = username
                data[_id] = r1

        return data


class list_users(base, aws._data_two_deep):
    datatype = "aws.iam.users"
    # Note: dumping a single_region object may cause non idempotent regions
    dump = True
    operator = "list_users"
    single_region = True
    r1_key = "Users"
    r2_id = "UserId"


class list_roles(base, aws._data_two_deep):
    datatype = "aws.iam.roles"
    operator = "list_roles"
    single_region = True
    r1_key = "Roles"
    r2_id = "RoleId"
