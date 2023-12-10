import gzip
import hashlib
import json
import os
import unicodedata
from base64 import b64decode

import boto3

from utils import get_logger

logger = get_logger()

ISSUE_TABLE = os.environ["ISSUE_TABLE"]
dynamodb = boto3.resource("dynamodb")
dynamodb_table = dynamodb.Table(ISSUE_TABLE)


def handler(event, _):
    """Lambda handlder for the detect_error function.

    This function will process CloudWatch logs via subscription filter events.
    It will infer uniqueness of a given error log by hashing the error message as the partition key and storing in DynamoDB.
    """
    logger.info(f"Processing event:", event)
    data = decode_data(event["awslogs"]["data"])
    data = json.loads(data)
    log_events = data["logEvents"]
    for log_event in log_events:
        message = log_event["message"]
        issue_hash = create_hash(message).hexdigest()
        put_issue(issue_hash, message)


def put_issue(issue_hash, message):
    """Store the issue_hash and message in DynamoDB.

    The use of update_item ensures that the dependant DynamoDB Stream can identify whether the item is new or existing.
    """
    logger.info(f"Updating issue {issue_hash} in DB")
    update_expression = "SET message = :message"
    expression_attribute_values = {":message": message}
    dynamodb_table.update_item(
        Key={
            "pk": issue_hash,
            "sk": issue_hash,
        },
        UpdateExpression=update_expression,
        ExpressionAttributeValues=expression_attribute_values,
    )


def create_hash(error_message):
    """Create a hash for an error message

    Assumed that the error message does not contain stateful information (i.e. date/time, variables).
    """
    return hashlib.md5(error_message.encode(), usedforsecurity=False)


def decode_data(encoded_zipped_data):
    """Decode zipped CloudWatch log record and convert to string."""
    zipped_data = b64decode(encoded_zipped_data)
    data = gzip.decompress(zipped_data)
    data = unicodedata.normalize("NFKD", data.decode("utf-8")).encode("ascii", "ignore")
    data = data.decode("utf-8")
    return data
