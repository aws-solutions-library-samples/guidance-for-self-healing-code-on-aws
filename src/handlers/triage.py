import os

import boto3

from utils import get_logger

WORKER_QUEUE_URL = os.environ.get("WORKER_QUEUE_URL")

logger = get_logger()
sqs_client = boto3.client("sqs")


def handler(event, _):
    """Lambda handler for the triage function.

    Process DynamoDB Stream events and enqueue any new items to SQS.
    """
    logger.info(f"Received event: {event}")
    for record in event["Records"]:
        if record["eventName"] == "INSERT":
            new_image = record["dynamodb"]["NewImage"]
            message = new_image["message"]["S"]
            logger.info(
                f"Detected new item (pk: {new_image['pk']['S']}, sk: {new_image['sk']['S']}), enqueuing message"
            )
            sqs_client.send_message(QueueUrl=WORKER_QUEUE_URL, MessageBody=message)
