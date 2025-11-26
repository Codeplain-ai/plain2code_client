import os
from typing import Optional, Union

from git import Repo

import file_utils

FUNCTIONAL_REQUIREMENT_IMPLEMENTED_COMMIT_MESSAGE = (
    "[Codeplain] Implemented code and unit tests for functional requirement {}"
)
REFACTORED_CODE_COMMIT_MESSAGE = "[Codeplain] Refactored code after implementing functional requirement {}"
CONFORMANCE_TESTS_PASSED_COMMIT_MESSAGE = (
    "[Codeplain] Fixed issues in the implementation code identified during conformance testing"
)

# Following messages are used as checkpoints in the git history
# Changing them will break backwards compatibility so change them with care
FUNCTIONAL_REQUIREMENT_FINISHED_COMMIT_MESSAGE = "[Codeplain] Functional requirement ID (FRID):{} fully implemented"
INITIAL_COMMIT_MESSAGE = "[Codeplain] Initial commit"
BASE_FOLDER_COMMIT_MESSAGE = "[Codeplain] Initialize build with Base Folder content"


RENDERED_FRID_MESSAGE = "Changes related to Functional requirement ID (FRID): {}"
RENDER_ID_MESSAGE = "Render ID: {}"


class InvalidGitRepositoryError(Exception):
    """Raised when the git repository is in an invalid state."""

    pass


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
    repo.git.commit("--allow-empty", "-m", INITIAL_COMMIT_MESSAGE)

    return repo


def is_dirty(repo_path: Union[str, os.PathLike]) -> bool:
    """Checks if the repository is dirty."""
    repo = Repo(repo_path)
    return repo.is_dirty(untracked_files=True)


def add_all_files_and_commit(
    repo_path: Union[str, os.PathLike], commit_message: str, frid: Optional[str] = None, render_id: Optional[str] = None
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


def revert_to_commit_with_frid(repo_path: Union[str, os.PathLike], frid: Optional[str] = None) -> Repo:
    """
    Finds commit with given frid mentioned in the commit message and reverts the branch to it.

    If frid argument is not provided (None), repo is reverted to the initial state. In case the base folder doesn't exist,
    code is reverted to the initial repo commit. Otherwise, the repo is reverted to the base folder commit.

    It is expected that the repo has at least one commit related to provided frid if frid is not None.
    In case the frid related commit is not found, an exception is raised.
    """
    repo = Repo(repo_path)

    commit = _get_commit(repo, frid)

    if not commit:
        raise InvalidGitRepositoryError("Git repository is in an invalid state. Relevant commit could not be found.")

    repo.git.reset("--hard", commit)
    repo.git.clean("-xdf")
    return repo


def checkout_commit_with_frid(repo_path: Union[str, os.PathLike], frid: Optional[str] = None) -> Repo:
    """
    Finds commit with given frid mentioned in the commit message and checks out that commit.

    If frid argument is not provided (None), repo is checked out to the initial state. In case the base folder doesn't exist,
    code is checked out to the initial repo commit. Otherwise, the repo is checked out to the base folder commit.

    It is expected that the repo has at least one commit related to provided frid if frid is not None.
    In case the frid related commit is not found, an exception is raised.
    """
    repo = Repo(repo_path)

    commit = _get_commit(repo, frid)

    if not commit:
        raise InvalidGitRepositoryError("Git repository is in an invalid state. Relevant commit could not be found.")

    repo.git.checkout(commit)
    return repo


def checkout_previous_branch(repo_path: Union[str, os.PathLike]) -> Repo:
    """
    Checks out the previous branch using 'git checkout -'.

    Args:
        repo_path (str | os.PathLike): Path to the git repository

    Returns:
        Repo: The git repository object
    """
    repo = Repo(repo_path)
    repo.git.checkout("-")
    return repo


def _get_diff_dict(diff_output: str) -> dict:
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

    commit = _get_commit(repo, previous_frid)

    # Add all files to the index to get a clean diff
    repo.git.add("-N", ".")

    # Get the raw git diff output, excluding .pyc files
    diff_output = repo.git.diff(commit, "--text", ":!*.pyc")

    if not diff_output:
        return {}

    return _get_diff_dict(diff_output)


def _get_commit(repo: Repo, frid: Optional[str]) -> str:
    if frid:
        commit = _get_commit_with_frid(repo, frid)
    else:
        commit = _get_base_folder_commit(repo)
        if not commit:
            commit = _get_initial_commit(repo)

    return commit


def _get_commit_with_frid(repo: Repo, frid: str) -> str:
    """Finds commit with given frid mentioned in the commit message."""
    commit = _get_commit_with_message(repo, FUNCTIONAL_REQUIREMENT_FINISHED_COMMIT_MESSAGE.format(frid))
    if not commit:
        raise InvalidGitRepositoryError(f"No commit with frid {frid} found.")
    return commit


def _get_base_folder_commit(repo: Repo) -> str:
    """Finds commit related to copy of the base folder."""
    return _get_commit_with_message(repo, BASE_FOLDER_COMMIT_MESSAGE)


def _get_initial_commit(repo: Repo) -> str:
    """Finds initial commit."""
    return _get_commit_with_message(repo, INITIAL_COMMIT_MESSAGE)


def _get_commit_with_message(repo: Repo, message: str) -> str:
    """Finds commit with given message."""
    escaped_message = message.replace("[", "\\[").replace("]", "\\]")

    return repo.git.rev_list(repo.active_branch.name, "--grep", escaped_message, "-n", "1")


def get_implementation_code_diff(repo_path: Union[str, os.PathLike], frid: str, previous_frid: str) -> dict:
    repo = Repo(repo_path)

    implementation_commit = _get_commit_with_message(repo, REFACTORED_CODE_COMMIT_MESSAGE.format(frid))
    if not implementation_commit:
        implementation_commit = _get_commit_with_message(
            repo, FUNCTIONAL_REQUIREMENT_IMPLEMENTED_COMMIT_MESSAGE.format(frid)
        )

    previous_frid_commit = _get_commit(repo, previous_frid)

    # Get the raw git diff output, excluding .pyc files
    diff_output = repo.git.diff(previous_frid_commit, implementation_commit, "--text", ":!*.pyc")

    if not diff_output:
        return {}

    return _get_diff_dict(diff_output)


def get_fixed_implementation_code_diff(repo_path: Union[str, os.PathLike], frid: str) -> dict:
    repo = Repo(repo_path)

    implementation_commit = _get_commit_with_message(repo, REFACTORED_CODE_COMMIT_MESSAGE.format(frid))
    if not implementation_commit:
        implementation_commit = _get_commit_with_message(
            repo, FUNCTIONAL_REQUIREMENT_IMPLEMENTED_COMMIT_MESSAGE.format(frid)
        )

    conformance_tests_passed_commit = _get_commit_with_message(
        repo, CONFORMANCE_TESTS_PASSED_COMMIT_MESSAGE.format(frid)
    )
    if not conformance_tests_passed_commit:
        return None

    # Get the raw git diff output, excluding .pyc files
    diff_output = repo.git.diff(implementation_commit, conformance_tests_passed_commit, "--text", ":!*.pyc")

    if not diff_output:
        return {}

    return _get_diff_dict(diff_output)
