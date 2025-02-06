import aws


class base(aws.base):
    service_name = "autoscaling"


class auto_scaling_groups(base, aws._data_two_deep):
    datatype = "aws.autoscaling.auto_scaling_groups"
    operator = "describe_auto_scaling_groups"
    r1_key = "AutoScalingGroups"
    r2_id = "AutoScalingGroupName"


class auto_scaling_instances(base, aws._data_two_deep):
    datatype = "aws.autoscaling.auto_scaling_instances"
    dump = True
    operator = "describe_auto_scaling_instances"
    r1_key = "AutoScalingInstances"
    r2_id = "InstanceId"


class notification_configurations(base, aws._data_two_deep):
    datatype = "aws.autoscaling.notification_configurations"
    operator = "describe_notification_configurations"
    r1_key = "NotificationConfigurations"
    r2_id = "NotificationType"


# class tags(base, aws._data_two_deep):
#     datatype = "aws.autoscaling.tags"
#     operator = "describe_tags"
#     r1_key = "Tags"
#     r2_id = ""
#
# Need to calculate the id from a number of other elements
