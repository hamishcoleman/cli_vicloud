"""Users and Perms (IAM)"""
import aws


_service_name = "iam"
datatype_prefix = "aws." + _service_name + "."


class base(aws.base):
    service_name = _service_name


class get_account_authorization_details(base, aws._data_two_deep):
    datatype = datatype_prefix + "account_authorization_details"
    # Note: dumping a single_region object may cause non idempotent regions
    dump = True
    operator = "get_account_authorization_details"
    single_region = True
    r1_key = "UserDetailList"
    r2_id = "UserName"


# get-credential-report / generate-credential-report

class list_access_keys(base):
    datatype = datatype_prefix + "access_keys"
    dump = True
    operator = "list_access_keys"
    single_region = True
    r1_key = "AccessKeyMetadata"
    r3_id = "AccessKeyId"

    def _fetch_one_client(self, client, args=None):
        datasource = client._datasource
        # first, get the list of users
        handler = list_users()
        handler.verbose = self.verbose
        users = handler._fetch_one_client(client)

        data = {}
        for _id, user in users.items():
            self.log_operator(datasource, self.operator)

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


class list_attached_group_policies(base):
    datatype = datatype_prefix + "attached_group_policies"
    dump = True
    operator = "list_attached_group_policies"
    single_region = True
    r1_key = "AttachedPolicies"

    def _fetch_one_client(self, client, args=None):
        datasource = client._datasource
        # first, get the list
        handler = list_groups()
        handler.verbose = self.verbose
        groups = handler._fetch_one_client(client)

        data = {}
        for _id, group in groups.items():
            self.log_operator(datasource, self.operator)

            groupname = group["GroupName"]
            kwargs = {
                "GroupName": groupname,
            }
            for r1 in self._paged_op(client, self.operator, **kwargs):
                del r1["ResponseMetadata"]
                del r1["IsTruncated"]
                data[_id] = r1

        return data


class list_attached_role_policies(base):
    datatype = datatype_prefix + "attached_role_policies"
    dump = True
    operator = "list_attached_role_policies"
    single_region = True
    r1_key = "AttachedPolicies"

    def _fetch_one_client(self, client, args=None):
        datasource = client._datasource
        # first, get the list
        handler = list_roles()
        handler.verbose = self.verbose
        roles = handler._fetch_one_client(client)

        data = {}
        for _id, role in roles.items():
            self.log_operator(datasource, self.operator)

            rolename = role["RoleName"]
            kwargs = {
                "RoleName": rolename,
            }
            for r1 in self._paged_op(client, self.operator, **kwargs):
                del r1["ResponseMetadata"]
                del r1["IsTruncated"]
                data[_id] = r1

        return data


class list_attached_user_policies(base):
    datatype = datatype_prefix + "attached_user_policies"
    dump = True
    operator = "list_attached_user_policies"
    single_region = True
    r1_key = "AttachedPolicies"

    def _fetch_one_client(self, client, args=None):
        datasource = client._datasource
        # first, get the list of users
        handler = list_users()
        handler.verbose = self.verbose
        users = handler._fetch_one_client(client)

        data = {}
        for _id, user in users.items():
            self.log_operator(datasource, self.operator)

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


# list-entities-for-policy


class list_groups(base, aws._data_two_deep):
    datatype = datatype_prefix + "groups"
    dump = True
    operator = "list_groups"
    single_region = True
    r1_key = "Groups"
    r2_id = "GroupName"


class list_groups_for_user(base):
    datatype = datatype_prefix + "groups_for_user"
    dump = True
    operator = "list_groups_for_user"
    single_region = True
    r1_key = "Groups"

    def _fetch_one_client(self, client, args=None):
        datasource = client._datasource
        # first, get the list of users
        handler = list_users()
        handler.verbose = self.verbose
        users = handler._fetch_one_client(client)

        data = {}
        for _id, user in users.items():
            self.log_operator(datasource, self.operator)

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


class list_mfa_devices(base):
    datatype = datatype_prefix + "mfa_devices"
    dump = True
    operator = "list_mfa_devices"
    single_region = True
    r1_key = "MFADevices"

    def _fetch_one_client(self, client, args=None):
        datasource = client._datasource
        # first, get the list of users
        handler = list_users()
        handler.verbose = self.verbose
        users = handler._fetch_one_client(client)

        data = {}
        for _id, user in users.items():
            self.log_operator(datasource, self.operator)

            username = user["UserName"]
            kwargs = {
                "UserName": username,
            }
            for r1 in self._paged_op(client, self.operator, **kwargs):
                del r1["ResponseMetadata"]
                del r1["IsTruncated"]
                data[_id] = r1

        return data


class list_instance_profiles(base, aws._data_two_deep):
    datatype = datatype_prefix + "instance_profiles"
    dump = True
    operator = "list_instance_profiles"
    single_region = True
    r1_key = "InstanceProfiles"
    r2_id = "InstanceProfileName"


class list_policies(base, aws._data_two_deep):
    datatype = datatype_prefix + "policies"
    dump = True
    operator = "list_policies"
    single_region = True
    r1_key = "Policies"
    r2_id = "PolicyName"


class list_role_tags(base):
    datatype = datatype_prefix + "role_tags"
    dump = True
    operator = "list_role_tags"
    single_region = True
    r1_key = "Tags"

    def _fetch_one_client(self, client, args=None):
        datasource = client._datasource
        # first, get the list of roles
        handler = list_roles()
        handler.verbose = self.verbose
        roles = handler._fetch_one_client(client)

        data = {}
        for _id, role in roles.items():
            self.log_operator(datasource, self.operator)

            rolename = role["RoleName"]
            kwargs = {
                "RoleName": rolename,
            }
            for r1 in self._paged_op(client, self.operator, **kwargs):
                for r2 in r1[self.r1_key]:
                    k = r2["Key"]
                    v = r2["Value"]

                    if rolename not in data:
                        data[rolename] = {}

                    data[rolename][k] = v
        return data


class list_roles(base, aws._data_two_deep):
    datatype = datatype_prefix + "roles"
    operator = "list_roles"
    single_region = True
    r1_key = "Roles"
    r2_id = "RoleName"


class list_saml_providers(base, aws._data_two_deep):
    datatype = datatype_prefix + "saml_providers"
    dump = True
    operator = "list_saml_providers"
    single_region = True
    r1_key = "SAMLProviderList"
    r2_id = "Arn"


class list_user_policies(base):
    datatype = datatype_prefix + "user_policies"
    dump = True
    operator = "list_user_policies"
    single_region = True
    r1_key = "PolicyNames"

    def _fetch_one_client(self, client, args=None):
        datasource = client._datasource
        # first, get the list of users
        handler = list_users()
        handler.verbose = self.verbose
        users = handler._fetch_one_client(client)

        data = {}
        for _id, user in users.items():
            self.log_operator(datasource, self.operator)

            username = user["UserName"]
            kwargs = {
                "UserName": username,
            }
            for r1 in self._paged_op(client, self.operator, **kwargs):
                del r1["ResponseMetadata"]
                del r1["IsTruncated"]
                data[_id] = r1

        return data


class list_user_tags(base):
    datatype = datatype_prefix + "user_tags"
    dump = True
    operator = "list_user_tags"
    single_region = True
    r1_key = "Tags"

    def _fetch_one_client(self, client, args=None):
        datasource = client._datasource
        # first, get the list of users
        handler = list_users()
        handler.verbose = self.verbose
        users = handler._fetch_one_client(client)

        data = {}
        for _id, user in users.items():
            self.log_operator(datasource, self.operator)

            username = user["UserName"]
            kwargs = {
                "UserName": username,
            }
            for r1 in self._paged_op(client, self.operator, **kwargs):
                for r2 in r1[self.r1_key]:
                    k = r2["Key"]
                    v = r2["Value"]

                    if username not in data:
                        data[username] = {}

                    data[username][k] = v
        return data


class list_users(base, aws._data_two_deep):
    datatype = datatype_prefix + "users"
    # Note: dumping a single_region object may cause non idempotent regions
    dump = True
    operator = "list_users"
    single_region = True
    r1_key = "Users"
    r2_id = "UserName"


class list_virtual_mfa_devices(base, aws._data_two_deep):
    datatype = datatype_prefix + "virtual_mfa_devices"
    dump = True
    operator = "list_virtual_mfa_devices"
    single_region = True
    r1_key = "VirtualMFADevices"
    r2_id = "SerialNumber"
