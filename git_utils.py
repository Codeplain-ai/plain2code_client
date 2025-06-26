import os
from typing import Union

from git import Repo

import file_utils

RENDERED_FRID_MESSAGE = "Changes related to Functional requirement ID (FRID): {}"
RENDER_ID_MESSAGE = "Render ID: {}"
BASE_FOLDER_COMMIT_MESSAGE = "Initialize build with Base Folder content"
REFACTORED_CODE_COMMIT_MESSAGE = "Refactored code after implementing {}"
CONFORMANCE_TESTS_PASSED_COMMIT_MESSAGE = (
    "Fixed issues in the implementation code identified during conformance testing"
)
FUNCTIONAL_REQUIREMENT_FINISHED_COMMIT_MESSAGE = "Functional requirement ID (FRID): {} fully implemented"

# The commit hash of the empty tree
EMPTY_TREE_COMMIT_HASH = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"


def init_git_repo(path_to_repo: Union[str, os.PathLike]) -> Repo:
    """
    Initializes a new git repository in the given path.
    If folder does not exist, it creates it.
    If the folder already exists, it deletes the content of the folder.
    """
    if os.path.isdir(path_to_repo):
        file_utils.delete_files_and_subfolders(path_to_repo)
    else:
        os.makedirs(path_to_repo)

    repo = Repo.init(path_to_repo)

    return repo


def is_dirty(repo_path: Union[str, os.PathLike]) -> bool:
    """Checks if the repository is dirty."""
    repo = Repo(repo_path)
    return repo.is_dirty(untracked_files=True)


def add_all_files_and_commit(
    repo_path: Union[str, os.PathLike], commit_message: str, frid: str = None, render_id: str = None
) -> Repo:
    """Adds all files to the git repository and commits them."""
    repo = Repo(repo_path)
    repo.git.add(".")

    message = f"{commit_message}"

    if frid or render_id:
        message += "\n\n" + "-" * 80

    if frid:
        message += f"\n\n{RENDERED_FRID_MESSAGE.format(frid)}"
    if render_id:
        message += f"\n\n{RENDER_ID_MESSAGE.format(render_id)}"

    # Check if there are any changes to commit
    if not repo.is_dirty(untracked_files=True):
        repo.git.commit("--allow-empty", "-m", message)
    else:
        repo.git.commit("-m", message)

    return repo


def revert_changes(repo_path: Union[str, os.PathLike]) -> Repo:
    """Reverts all changes made since the last commit."""
    repo = Repo(repo_path)
    repo.git.reset("--hard")
    repo.git.clean("-xdf")
    return repo


def revert_to_commit_with_frid(repo_path: Union[str, os.PathLike], frid: str) -> Repo:
    """Finds commit with given frid mentioned in the commit message and reverts the branch to it."""
    repo = Repo(repo_path)
    commit = _get_commit_with_frid(repo, frid)
    repo.git.reset("--hard", commit)
    repo.git.clean("-xdf")
    return repo


def diff(repo_path: Union[str, os.PathLike], previous_frid: str = None) -> dict:
    """
    Get the git diff between the current code state and the previous frid using git's native diff command.
    If previous_frid is not provided, we try to find the commit related to the copy of the base folder.
    Removes the 'diff --git' and 'index' lines to get clean unified diff format.


    Args:
        repo_path (str | os.PathLike): Path to the git repository
        previous_frid (str): Functional requirement ID (FRID) of the previous commit

    Returns:
        dict: Dictionary with file names as keys and their clean diff strings as values
    """
    repo = Repo(repo_path)

    if previous_frid:
        commit = _get_commit_with_frid(repo, previous_frid)
    else:
        commit = _get_base_folder_commit(repo)

    # Add all files to the index to get a clean diff
    repo.git.add("-N", ".")

    # Get the raw git diff output, excluding .pyc files
    if not commit:
        # If there is no base commit, we are listing all files as new
        diff_output = repo.git.diff(EMPTY_TREE_COMMIT_HASH, "--text", ":!*.pyc")
    else:
        diff_output = repo.git.diff(commit, "--text", ":!*.pyc")

    if not diff_output:
        return {}

    diff_dict = {}
    current_file = None
    current_diff_lines = []

    lines = diff_output.split("\n")
    i = 0

    while i < len(lines):
        line = lines[i]

        if line.startswith("diff --git"):
            # Save previous file's diff if exists
            if current_file and current_diff_lines:
                diff_dict[current_file] = "\n".join(current_diff_lines)

            # Extract file name from diff --git line
            parts = line.split(" ")
            if len(parts) >= 4:
                # Get the b/ path (new file path)
                current_file = parts[3][2:] if parts[3].startswith("b/") else parts[3]
            current_diff_lines = []

            # Skip the diff --git line
            i += 1

            # Skip the index line if it exists
            while i < len(lines) and (
                lines[i].startswith("index ")
                or lines[i].startswith("new file mode ")
                or lines[i].startswith("deleted file mode ")
            ):
                i += 1

            continue

        # Add all other lines to current diff
        if current_file is not None:
            current_diff_lines.append(line)

        i += 1

    # Don't forget the last file
    if current_file and current_diff_lines:
        diff_dict[current_file] = "\n".join(current_diff_lines)

    return diff_dict


def _get_commit_with_frid(repo: Repo, frid: str) -> str:
    """Finds commit with given frid mentioned in the commit message."""
    current_branch = repo.active_branch.name
    commit = repo.git.rev_list(
        current_branch, "--grep", FUNCTIONAL_REQUIREMENT_FINISHED_COMMIT_MESSAGE.format(frid), "-n", "1"
    )
    if not commit:
        raise Exception(f"No commit with frid {frid} found.")
    return commit


def _get_base_folder_commit(repo: Repo) -> str:
    """Finds commit related to copy of the base folder."""
    current_branch = repo.active_branch.name
    return repo.git.rev_list(current_branch, "--grep", BASE_FOLDER_COMMIT_MESSAGE, "-n", "1")
