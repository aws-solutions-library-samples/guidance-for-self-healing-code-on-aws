# Log Driven Bug Fixer repo (self-healing code)
This repo includes an end-to-end system to automatically remediate bugs.

It ingests application logs from Amazon CloudWatch Logs into AWS Lambda, which then generates a GenAI prompt to suggest code fixes. The code fix is committed to source code and presented to the end user as a pull request in Github.

The AI models and providers are intended to be interchangeable. Currently supported providers and models are Amazon Bedrock (Claudev1) and OpenAI (GPT-3.5).

## Dependencies
- AWS SAM
- Python 3.9

## Deployment
Export the required environment variables:
```
export STACK_NAME=log-driven-bug-fixer

# All variables and secrets for this project will be stored under this prefix.
# You can define a different value if it's already in use.
export PARAMETER_STORE_PREFIX=${STACK_NAME}/
```

Install Python dependencies and run the configuration wizard to securely store variables and secrets in SSM Parameter Store:
```
pip install -r requirements.txt
bin/configure.py
```
Re-run the above script if you need to make any changes. Alternatively, you can directly modify the SSM Parameter Store values which are stored under the ${PARAMETER_STORE_PREFIX} prefix.

Deploy the AWS resources:
```
sam/deploy.sh
```

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.
