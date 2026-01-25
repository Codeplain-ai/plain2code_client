import os

import pytest

os.environ["MASTER_KEY"] = "test-master-key"
os.environ["GOOGLE_API_KEY"] = "test-google-api-key"


@pytest.fixture
def test_data_path():
    """Returns the path to the test data directory."""
    return os.path.dirname(__file__)


@pytest.fixture
def load_test_data(test_data_path):
    """Returns a function to load test data files."""

    def _load(file_name):
        file_path = os.path.join(test_data_path, file_name)
        with open(file_path, "r") as file:
            return file.read()

    return _load


@pytest.fixture
def get_test_data_path(test_data_path):
    """Returns a function to get the path to a test data subfolder."""

    def _get_path(subfolder_name):
        return os.path.join(test_data_path, subfolder_name)

    return _get_path
