import os
import shutil
import sys

import yaml

from plain2code_console import console


class SystemRequirements:
    """Manages and validates system-level requirements for the application."""

    def __init__(self):
        self.requirements = self._load_requirements()

    def _load_requirements(self):
        """Load system requirements from YAML file."""
        config_path = os.path.join(os.path.dirname(__file__), "system_requirements.yaml")
        try:
            with open(config_path, "r") as f:
                yaml_data = yaml.safe_load(f)
                if "system_requirements" not in yaml_data:
                    raise KeyError("Missing 'system_requirements' key in config file")
                return yaml_data["system_requirements"]
        except Exception as e:
            console.error(f"Failed to load system requirements: {e}")
            sys.exit(69)

    def verify_requirements(self):
        """Verify all system requirements are met."""
        for req_data in self.requirements.values():
            if not shutil.which(req_data["command"]):
                console.error(req_data["error_message"])
                sys.exit(69)
