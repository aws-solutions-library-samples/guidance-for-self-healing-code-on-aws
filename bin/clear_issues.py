import os

import boto3

ISSUE_TABLE_OUTPUT_KEY = "IssueTableName"


def get_table_name_from_cf_output(stack_name):
    cloudformation = boto3.client("cloudformation")

    response = cloudformation.describe_stacks(StackName=stack_name)

    for output in response["Stacks"][0]["Outputs"]:
        if output["OutputKey"] == ISSUE_TABLE_OUTPUT_KEY:
            return output["OutputValue"]

    return None


def run():
    stack_name = os.environ["STACK_NAME"]
    table_name = get_table_name_from_cf_output(stack_name)
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(table_name)

    scan = table.scan()

    with table.batch_writer() as batch:
        for item in scan["Items"]:
            batch.delete_item(
                Key={
                    "pk": item["pk"],
                    "sk": item["sk"],
                }
            )

    print(f"Deleted all issues from table {table_name}")


if __name__ == "__main__":
    run()
