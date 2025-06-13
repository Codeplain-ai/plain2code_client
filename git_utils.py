from git import Repo

RENDERED_FRID_MESSAGE = "Changes related to Functional requirement ID (FRID): {}"
BASE_FOLDER_COMMIT_MESSAGE = "Initialize build with Base Folder content"

# The commit hash of the empty tree
EMPTY_TREE_COMMIT_HASH = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"


def init_clean_repo(repo_path):
    """Initializes a new git repository in the given path."""
    repo = Repo.init(repo_path)

    return repo


def is_dirty(repo_path):
    """Checks if the repository is dirty."""
    repo = Repo(repo_path)
    return repo.is_dirty(untracked_files=True)


def add_all_files_and_commit(repo_path, commit_message, frid):
    """Adds all files to the git repository and commits them."""
    repo = Repo(repo_path)
    repo.git.add(".")

    message = f"{commit_message}\n\n{RENDERED_FRID_MESSAGE.format(frid)}" if frid else commit_message

    # Check if there are any changes to commit
    if not repo.is_dirty(untracked_files=True):
        repo.git.commit("--allow-empty", "-m", message)
    else:
        repo.git.commit("-m", message)

    return repo


def revert_changes(repo_path):
    """Reverts all changes made since the last commit."""
    repo = Repo(repo_path)
    repo.git.reset("--hard")
    repo.git.clean("-xdf")
    return repo


def revert_to_commit_with_frid(repo_path, frid):
    """Finds commit with given frid mentioned in the commit message and reverts the branch to it."""
    repo = Repo(repo_path)
    commit = _get_commit_with_frid(repo, frid)
    repo.git.reset("--hard", commit)
    repo.git.clean("-xdf")
    return repo


def diff(repo_path, previous_frid=None):
    """
    Get the git diff between the current code state and the previous frid using git's native diff command.
    If previous_frid is not provided, we try to find the commit related to the copy of the base folder.
    Removes the 'diff --git' and 'index' lines to get clean unified diff format.


    Args:
        repo_path (str): Path to the git repository

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


def _get_commit_with_frid(repo, frid):
    """Finds commit with given frid mentioned in the commit message."""
    commit = repo.git.rev_list("main", "--grep", RENDERED_FRID_MESSAGE.format(frid), "-n", "1")
    if not commit:
        raise Exception(f"No commit with frid {frid} found.")
    return commit


def _get_base_folder_commit(repo):
    """Finds commit related to copy of the base folder."""
    return repo.git.rev_list("main", "--grep", BASE_FOLDER_COMMIT_MESSAGE, "-n", "1")
