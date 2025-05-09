"""Contains all state and context information we need for the rendering process."""

import copy
import json
import os
import shutil
from typing import Optional

import file_utils
from plain2code_console import console


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


class ExecutionState:
    """Manages the counter of retries for a given functional requirement."""

    MAX_CONFORMANCE_TESTING_RENDERING_RETRIES = 2  # We're retrying 2 times failed conformance testing

    def __init__(self):
        self.conformance_testing_rendering_retries = 0

    def mark_failed_conformance_testing_rendering(self):
        self.conformance_testing_rendering_retries += 1

    def should_rerender_functional_requirement(self):
        return self.conformance_testing_rendering_retries < self.MAX_CONFORMANCE_TESTING_RENDERING_RETRIES


class ConformanceTestsState:
    """Manages the state of conformance tests."""

    def __init__(
        self,
        conformance_tests_folder: str,
        backup_folder_suffix: str,
        is_first_frid: bool,
        conformance_tests_definition_file_name: str,
        conformance_tests_script: str,
        verbose: bool,
        debug: bool,
        dry_run: bool,
    ):
        self.conformance_tests_folder = conformance_tests_folder
        self.backup_folder_suffix = backup_folder_suffix
        self.conformance_tests_backup_folder = self.conformance_tests_folder + self.backup_folder_suffix
        # If it's the first FRID, we possibly won't have neither conformance tests nor backup folder.
        # In all the other cases, we can rest assured that both the conformance tests and the backup folder exist
        # (and if they don't, this indicates a bug // wierd state in the codebase)
        self.is_first_frid = is_first_frid
        # Just a state through which we keep track if we're able to call method restore_from_backup
        self._initialized_backup_folder = False
        self.conformance_tests_definition_file_name = conformance_tests_definition_file_name
        self.full_conformance_tests_definition_file_name = os.path.join(
            self.conformance_tests_folder, self.conformance_tests_definition_file_name
        )
        self.verbose = verbose
        self.debug = debug
        self.conformance_tests_script = conformance_tests_script
        self.dry_run = dry_run

    def _ensure_folder_validity(self, folder: str):
        """
        Validator that checks if the folder states are valid.
        Exceptions:
        - No conformance test script is passed, so we won't do anything with the conformance tests folder, so we just don't need it.
        - It's the first FRID, so we haven't yet started conformance tests, so they may not exist.
        """
        if not self.conformance_tests_script:
            return

        if not os.path.exists(folder):
            if not self.is_first_frid:
                raise Exception(f"{folder} not found.")
            else:
                return

    def init_backup_folder(self):
        """
        Initialize the backup folder.
        - If conformance tests folder exists, we copy the contents of conformance folder into the backup folder
        - If conformance tests folder doesn't exist, we create a blank directory.
        """
        self._initialized_backup_folder = True

        if self.dry_run:
            if self.debug:
                console.info("Dry run, so initialization of backup folder skipped.")
            return

        if not self.conformance_tests_script:
            if self.debug:
                console.info("No conformance tests script, so initialization of backup folder skipped.")
            return

        self._ensure_folder_validity(self.conformance_tests_folder)

        if os.path.exists(self.conformance_tests_folder):
            if os.path.exists(self.conformance_tests_backup_folder):
                shutil.rmtree(self.conformance_tests_backup_folder)

            shutil.copytree(self.conformance_tests_folder, self.conformance_tests_backup_folder)

            if self.verbose:
                console.info("Conformance tests folder successfully backed up.")
        else:
            if self.verbose:
                console.info("Conformance tests folder doesn't exist, so creating a blank directory.")
            os.makedirs(self.conformance_tests_folder)
            if not os.path.exists(self.conformance_tests_backup_folder):
                os.makedirs(self.conformance_tests_backup_folder)

    def restore_from_backup(self):
        """
        Restore the conformance tests from the backup folder.

        Assumptions we make:
        - You've called `init_backup_folder` first and only then restore.
        - Backup folder exists.
        """
        if not self._initialized_backup_folder:
            raise Exception(
                "Backup folder not initialized yet. Call method `init_backup_folder` first and only then restore."
            )

        if self.dry_run:
            # this shouldn't happen, since dry run returns before this method is called, but just to make sure
            if self.debug:
                console.info("Dry run, so restoring from backup skipped.")
            return

        if not self.conformance_tests_script:
            if self.debug:
                console.info("No conformance tests script, so restoring from backup skipped.")
            return

        self._ensure_folder_validity(self.conformance_tests_backup_folder)

        # nonexistent backup folder is unexpected state since we ensure being called after init_backup_folder
        if not os.path.exists(self.conformance_tests_backup_folder):
            raise Exception(f"{self.conformance_tests_backup_folder} not found.")

        # Remove the existing conformance tests folder if exists
        if os.path.exists(self.conformance_tests_folder):
            shutil.rmtree(self.conformance_tests_folder)

        shutil.copytree(self.conformance_tests_backup_folder, self.conformance_tests_folder)

    def get_conformance_tests_json(self):
        try:
            with open(self.full_conformance_tests_definition_file_name, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def dump_conformance_tests_json(self, conformance_tests_json: dict):
        """Dump the conformance tests definition to the file."""
        if os.path.exists(self.conformance_tests_folder):
            if self.verbose:
                console.info(
                    f"Storing conformance tests definition to {self.full_conformance_tests_definition_file_name}"
                )
            with open(self.full_conformance_tests_definition_file_name, "w") as f:
                json.dump(conformance_tests_json, f, indent=4)
