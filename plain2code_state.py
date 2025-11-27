"""Contains all state and context information we need for the rendering process."""

import json
import os
import uuid
from typing import Optional

from plain2code_console import console

CONFORMANCE_TESTS_DEFINITION_FILE_NAME = "conformance_tests.json"


class ConformanceTestsUtils:
    """Manages the state of conformance tests."""

    def __init__(
        self,
        conformance_tests_folder: str,
        conformance_tests_definition_file_name: str,
        verbose: bool,
    ):
        self.conformance_tests_folder = conformance_tests_folder
        self.full_conformance_tests_definition_file_name = os.path.join(
            self.conformance_tests_folder, conformance_tests_definition_file_name
        )
        self.verbose = verbose

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


class RunState:
    """Contains information about the identifiable state of the rendering process."""

    def __init__(self, spec_filename: str, replay_with: Optional[str] = None):
        self.replay: bool = replay_with is not None
        if replay_with:
            self.render_id: str = replay_with
        else:
            self.render_id: str = str(uuid.uuid4())
        self.spec_filename: str = spec_filename
        self.call_count: int = 0
        self.unittest_batch_id: int = 0
        self.frid_render_anaysis: dict[str, str] = {}

    def increment_call_count(self):
        self.call_count += 1

    def increment_unittest_batch_id(self):
        self.unittest_batch_id += 1

    def add_rendering_analysis_for_frid(self, frid, rendering_analysis) -> None:
        self.frid_render_anaysis[frid] = rendering_analysis

    def to_dict(self):
        return {
            "render_id": self.render_id,
            "call_count": self.call_count,
            "replay": self.replay,
            "spec_filename": self.spec_filename,
        }
