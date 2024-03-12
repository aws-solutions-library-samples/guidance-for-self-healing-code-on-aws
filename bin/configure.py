import os
import re

import boto3

PROMPTS = {
    "repo_url": {
        "prompt": "Enter the target repository's SSH URL (i.e. git@github.com:foo/bar.git). This is the code repo for your application",
        "default": None,
    },
    "repo_api_key": {
        "prompt": "Enter the target repository's API key/access token (i.e. ghp_xxxxx). For github repos, please refer this link for creating an access token. https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens",
        "default": None,
    },
    "repo_ssh_private_key": {
        "prompt": "Enter an SSH private key that has write permissions to the target repository (i.e. \n-----BEGIN OPENSSH PRIVATE KEY-----\nb3BlbnN...em9uLmNvbQECAw==\n-----END OPENSSH PRIVATE KEY-----\n)",
        "default": None,
        "multiline": True,
    },
    "cloudwatch_log_group_name": {
        "prompt": "Enter the CloudWatch log group name for your existing application",
        "default": None,
    },
}


def prompt_user_for_multiline(prompt):
    """Prompt the user for a multiline text block."""
    print(prompt + " (Enter multiple lines. End with a blank line):")
    lines = []
    while True:
        line = input()
        if line:
            lines.append(line)
        else:
            break

    return "\n".join(lines) + "\n"


# Function to extract Repo Name from a git URL
def get_repo_name(git_url):
    strPattern = "([^/]+)\\.git$"
    pattern = re.compile(strPattern)
    matcher = pattern.search(git_url)
    return matcher.group(1).replace(".git", "")


def get_repo_project(git_url):
    pattern = r"https://github.com/([^/]+)/([^/]+)"
    match = re.match(pattern, git_url)
    if match:
        return match.group(1)
    return None


def run(prefix):
    """Prompt the user for variables and secrets which will be stored under an SSM Parameter Store prefix."""
    # Dictionary to store the responses
    parameters = {}

    # Prompt the user for each value with a default
    for key, prompt_info in PROMPTS.items():
        if prompt_info.get("default"):
            default_text = f" [{prompt_info['default']}]"
        else:
            default_text = ""

        while True:
            if prompt_info.get("multiline"):
                user_input = prompt_user_for_multiline(prompt_info["prompt"])
            else:
                user_input = input(f"{prompt_info['prompt']}{default_text}: ")
            if user_input or prompt_info["default"] is not None:
                parameters[key] = user_input if user_input else prompt_info["default"]
                break

    # Extract the repo name and project from the repo URL
    repo_name = get_repo_name(parameters["repo_url"])
    parameters["repo_name"] = repo_name
    project = get_repo_project(parameters["repo_url"])
    parameters["repo_api_url"] = f"https://api.github.com/repos/{project}/{repo_name}"

    # Store the values in SSM Parameter Store
    ssm = boto3.client("ssm")
    for key, value in parameters.items():
        if not value:
            continue

        parameter_name = f"{prefix}{key}"
        print(f"Putting parameter {parameter_name}")
        ssm.put_parameter(
            Name=parameter_name,
            Value=value,
            Type="SecureString",
            Overwrite=True,
        )

    return parameters


if __name__ == "__main__":
    try:
        prefix = os.environ["PARAMETER_STORE_PREFIX"]
    except KeyError:
        print(
            "PARAMETER_STORE_PREFIX variable not defined. Export this value and run the command again (i.e. export PARAMETER_STORE_PREFIX=self-healing-code/)"
        )
        exit(1)

    run(prefix)
