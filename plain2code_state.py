"""Contains all state and context information we need for the rendering process."""

import copy
import os
from typing import Optional

import file_utils


class Codebase:
    """Manages the state of the codebase at different points in the rendering process."""

    def __init__(self):
        self.existing_files = None
        self.changed_files = None
        self.existing_files_content = None

    def save_state(self, existing_files, changed_files, build_folder: Optional[str] = None):
        """Capture the current state of the codebase using deepcopy."""
        self.existing_files = copy.deepcopy(existing_files)
        self.changed_files = copy.deepcopy(changed_files)
        if build_folder:
            self.existing_files_content = copy.deepcopy(
                file_utils.get_existing_files_content(build_folder, existing_files)
            )
        else:
            self.existing_files_content = dict()

    def restore_state(self, build_folder):
        """Restore the codebase to the captured state."""
        if self.existing_files is None or self.changed_files is None or self.existing_files_content is None:
            raise ValueError(
                "Cannot restore state: state not properly captured - missing one of the following: existing_files, changed_files, existing_files_content"
            )

        # Remove files not in the snapshot
        current_files = set(file_utils.list_all_text_files(build_folder))
        snapshot_files = set(self.existing_files)
        for file_to_remove in current_files - snapshot_files:
            os.remove(os.path.join(build_folder, file_to_remove))

        # Restore file contents
        for fname, content in self.existing_files_content.items():
            with open(os.path.join(build_folder, fname), "w") as f:
                f.write(content)

        return copy.deepcopy(self.existing_files), copy.deepcopy(self.changed_files)
