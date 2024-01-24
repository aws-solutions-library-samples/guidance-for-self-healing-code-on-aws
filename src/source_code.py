import os
from abc import ABC, abstractmethod

import requests
from black import FileMode, format_str
from git import Repo

from utils import get_logger

logger = get_logger()


def clone_repo(url, repo_dir, ssh_private_key_path):
    """Clone the target repo to the local file system."""
    logger.info(f"Cloning repo {url} to {repo_dir}")
    repo = Repo.clone_from(
        url,
        repo_dir,
        env={
            "GIT_SSH_COMMAND": f"ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -i {ssh_private_key_path}"
        },
    )
    repo.config_writer().set_value("user", "name", "fix-code-bot").release()
    repo.config_writer().set_value("user", "email", "fix@code.bot").release()
    return repo


def update_source_code(files, repo_dir, format_code=True):
    """Overwrite files in target repo."""
    logger.info(f"Updating source code in {repo_dir}")
    for file in files:
        if format_code:
            contents = format(file["contents"])
        with open(os.path.join(repo_dir, file["filename"]), "w") as f:
            logger.info(f'Writing to {file["filename"]}')
            f.write(contents)


def format(content):
    """Format code."""
    return format_str(content, mode=FileMode())


def create_branch(branch_name, repo, commit_message):
    """Check for any changes to the source code and create a branch."""
    if repo.index.diff(None):
        logger.info(
            f"Source code has been modified, committing changes to branch {branch_name}"
        )
        new_branch = repo.create_head(branch_name)
        new_branch.checkout()
        repo.git.add(A=True)
        repo.git.commit(m=commit_message)
        logger.info(f"Pushing branch {branch_name}")
        repo.git.push("origin", branch_name)
        return True


class GitProvider(ABC):
    @abstractmethod
    def create_pull_request(branch_name):
        pass


class GitHubProvider(GitProvider):
    """GitHub provider.

    Interacts with the GitHub API to perform git operations.
    """

    def __init__(self, api_key, repo_url):
        self.url = f"{repo_url}/pulls"
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def create_pull_request(self, branch, title, description):
        """Create a new pull request for a target branch"""
        data = {
            "title": title,
            "body": description,
            "head": branch,
            "base": "main",
        }

        response = requests.post(self.url, json=data, headers=self.headers, timeout=30)

        if response.status_code == 201:
            logger.info(f"Pull request created ({response.json()['html_url']})")
        else:
            logger.info(f"Failed to create pull request with error: {response.text}")
