#! /bin/bash
set -e
SCRIPT=$(realpath "$0")
cd $(dirname "$SCRIPT")

echo "Retrieving target CloudWatch Log group name from Parameter Store"
CLOUDWATCH_LOG_GROUP_NAME=$(aws ssm get-parameter --name "${PARAMETER_STORE_PREFIX}cloudwatch_log_group_name" --with-decryption --query "Parameter.Value" --output text)

cp template.yaml ../.build
cd ../.build

echo "Creating deployment package"
aws cloudformation package \
    --template-file template.yaml \
    --s3-bucket ${DEPLOYMENT_S3_BUCKET} \
    --s3-prefix ${STACK_NAME} \
    --output-template-file template-packaged.yaml

aws cloudformation deploy \
    --stack-name ${STACK_NAME} \
    --template-file template-packaged.yaml \
    --capabilities CAPABILITY_NAMED_IAM \
    --parameter-overrides \
    ParameterStorePrefix=${PARAMETER_STORE_PREFIX} \
    CloudWatchLogGroupName=${CLOUDWATCH_LOG_GROUP_NAME} \
    --tags Name=${STACK_NAME}
