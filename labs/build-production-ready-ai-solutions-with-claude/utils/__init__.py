import boto3


def get_param_value(parameter_name):
    """Return str parameter value from SSM Parameter Store"""
    ssm = boto3.client('ssm')
    response = ssm.get_parameter(
            Name=parameter_name
        )
    return response['Parameter']['Value']