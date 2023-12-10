import logging

import boto3


def get_logger():
    """Configure a logger compatible with local python interpreter and Lambda."""
    if len(logging.getLogger().handlers) > 0:
        # The Lambda environment pre-configures a handler logging to stderr. If a handler is already configured,
        # `.basicConfig` does not execute. Thus we set the level directly.
        logging.getLogger().setLevel(logging.INFO)
    else:
        logging.basicConfig(level=logging.INFO)
    return logging.getLogger()


def get_config(parameter_store_prefix, parameter_names):
    """Build a config object from parameter store values.

    Withdraw the prefix value from the returned config object.
    """
    ssm = boto3.client("ssm")
    prefixed_parameter_names = [
        f"{parameter_store_prefix}{parameter_name}"
        for parameter_name in parameter_names
    ]
    response = ssm.get_parameters(
        Names=prefixed_parameter_names,
        WithDecryption=True,  # Set to True if any parameters are encrypted
    )

    config = {}
    for param in response.get("Parameters", []):
        config_item_name = param["Name"].split(parameter_store_prefix)[-1]
        config[config_item_name] = param["Value"]

    return config
