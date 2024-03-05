import os
import re
import tempfile
import time

from providers.bedrock import Claude
from source_code import GitHubProvider, clone_repo, create_branch, update_source_code
from utils import get_config, get_logger

logger = get_logger()

PARAMETER_NAMES = (
    "model_provider",
    "repo_url",
    "repo_name",
    "repo_api_url",
    "repo_api_key",
    "repo_ssh_private_key",
    "cloudwatch_log_group_name",
)
PARAMETER_STORE_PREFIX = os.environ["PARAMETER_STORE_PREFIX"]
MODEL_AWS_REGION = "us-east-1"

SSH_PRIVATE_KEY_FILENAME = "ssh_private_key"


def handler(event, context):
    """Lambda handler for the fix_code function.

    Takes the stack trace from the event and prompts GenAI to provide a fix.
    This Lambda will:
    - Parse a stack trace from the event
    - Retrieve the source code from git repo
    - Create a prompt including the stack trace and minified source code to send to AI model
    - Create a pull request to fix the code
    """
    logger.info(f"Processing event: {event}")
    error_context = event["Records"][0]["body"]

    logger.info(f"Retrieving config")
    config = get_config(PARAMETER_STORE_PREFIX, PARAMETER_NAMES)

    # Select a model provider to perform the code generation
    if config["model_provider"] == "bedrock":
        provider = Claude(model_aws_region=MODEL_AWS_REGION)
    else:
        raise Exception(f"Invalid model provider: {config['model_provider']}")
    logger.info(f"Using model provider: {config['model_provider']}")

    # Prepare SSH credentials for cloning the target repo
    tmpdir = tempfile.mkdtemp()
    ssh_private_key = os.path.join(tmpdir, "ssh_private_key")
    write_ssh_key(config["repo_ssh_private_key"], ssh_private_key)

    # Clone the target repo
    git_provider = GitHubProvider(config["repo_api_key"], config["repo_api_url"])
    target_repo_dir = os.path.join(tmpdir, context.aws_request_id, config["repo_name"])
    repo = clone_repo(config["repo_url"], target_repo_dir, ssh_private_key)

    # Extract filenames relevant to the error from stack trace
    filenames = get_filenames_from_stack_trace(error_context, repo)

    # Create a map of relevant filenames with the actual filenames in the target repo
    source_code_map = create_source_code_map(target_repo_dir, filenames)

    # Trigger the code generation
    result = provider.fix_code(error_context, source_code_map)

    # Modify the local cloned repo with the generated code
    update_source_code(result["source_code"], target_repo_dir)

    # Create a branch and commit/push the code to the source repo
    branch_name = f"fix-code-{round(time.time())}"
    branch_created = create_branch(branch_name, repo, result["description"])
    if not branch_created:
        logger.info("No changes were made, exiting.")
        return

    # Create a pull request
    git_provider.create_pull_request(
        branch_name, result["title"], result["description"]
    )


def write_ssh_key(value, file_path):
    """Retrieve git SSH private key from SSM and write to file."""
    logger.info(f"Writing SSH key to {file_path}")
    with open(file_path, "w") as f:
        f.write(value)
    os.chmod(file_path, int("600", base=8))


def get_filenames_from_stack_trace(stack_trace, repo):
    """Perform regex match to match filenames containing repo_name in stack_trace.
    Return relative paths to files from repo root.
    """
    file_paths_in_repo = [entry.path for entry in repo.commit().tree.traverse()]

    # This regex should work for both Python and Javascript files
    file_path_pattern = r'(?:File "([^"]+)"|at \S+ \(file://([^:]+):\d+:\d+\))'
    file_paths = re.findall(file_path_pattern, stack_trace)

    # Extract the non-empty file paths from the matches
    file_paths = [path[0] if path[0] else path[1] for path in file_paths]

    matching_repo_file_paths = find_partial_matches(file_paths, file_paths_in_repo)
    return matching_repo_file_paths


def find_partial_matches(primary_paths, secondary_paths):
    """Find and return partial matches between file paths in two lists based on filenames.

    This function compares file paths in the `primary_paths` list to those in the `secondary_paths` list
    and returns a list of partial matches if matching filenames are found, regardless of the root directory.

    Example:
        primary_paths = [
            '/var/task/handlers/create_order.py'
        ]
        secondary_paths = [
            '.gitignore',
            'README.md',
            'src',
            'template.yaml',
            'src/handlers',
            'src/requirements.txt',
            'src/handlers/create_order.py',
            'src/handlers/sample.py'
        ]
        results = find_partial_matches(primary_paths, secondary_paths)

    Returns:
        ['src/handlers/sample.py'] if a partial match is found, or an empty list if no matches are found.
    """
    results = []

    for primary_path in primary_paths:
        primary_filename = os.path.basename(primary_path)
        for secondary_path in secondary_paths:
            secondary_filename = os.path.basename(secondary_path)
            if primary_filename == secondary_filename:
                results.append(secondary_path)

    return results


def create_source_code_map(repo_dir, filenames):
    """Create a map of relevant filenames with the actual filenames in the target repo."""
    logger.info(f"Creating source code map for {filenames}")
    source_code_map = {}
    for filename in filenames:
        with open(os.path.join(repo_dir, filename), "r") as f:
            source_code_map[filename] = f.read()
    return source_code_map


if __name__ == "__main__":

    class MockContext:
        aws_request_id = "1234"

    error = """
         [ERROR] KeyError: \'order_items\'\nTraceback (most recent call last):\n  File "/var/task/handlers/create_order.py", line 14, in handler\n    order_items = body["order_items"]
         """
    handler(
        {"Records": [{"body": error}]},
        MockContext(),
    )
