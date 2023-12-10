#! /bin/bash

set -e

SCRIPT=$(realpath "$0")
cd $(dirname "$SCRIPT")

CLOUDWATCH_LOG_GROUP_NAME=$(aws ssm get-parameter --name "${PARAMETER_STORE_PREFIX}cloudwatch_log_group_name" --with-decryption --query "Parameter.Value" --output text)

sam build -u

sam deploy \
    --stack-name ${STACK_NAME} \
    --resolve-s3 \
    --capabilities CAPABILITY_NAMED_IAM \
    --parameter-overrides \
    ParameterStorePrefix=${PARAMETER_STORE_PREFIX} \
    CloudWatchLogGroupName=${CLOUDWATCH_LOG_GROUP_NAME} \
    --tags Name=${STACK_NAME}
