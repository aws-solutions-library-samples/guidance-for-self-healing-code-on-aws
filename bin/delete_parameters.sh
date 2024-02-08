#! /bin/bash

parameters=$(aws ssm describe-parameters --query "Parameters[?starts_with(Name, '${PARAMETER_STORE_PREFIX}')].Name" --output text)

for param in $parameters; do
    aws ssm delete-parameter --name "$param"
done
