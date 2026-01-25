import pytest

import plain_file


def test_non_existent_require(get_test_data_path):
    with pytest.raises(Exception, match="Required module not found"):
        plain_file.plain_file_parser("non_existent_require.plain", [get_test_data_path("data/requires")])


def test_independent_requires(get_test_data_path):
    with pytest.raises(Exception, match="There must be a fixed order how required modules are dependent"):
        plain_file.plain_file_parser("independent_requires_main.plain", [get_test_data_path("data/requires")])


def test_diamond_requires(get_test_data_path):
    with pytest.raises(Exception, match="There must be a fixed order how required modules are dependent"):
        plain_file.plain_file_parser("diamond_requires_main.plain", [get_test_data_path("data/requires")])


def test_circular_requires(get_test_data_path):
    with pytest.raises(Exception, match="Circular required module detected"):
        plain_file.plain_file_parser("circular_requires_main.plain", [get_test_data_path("data/requires")])


def test_normal_requires(get_test_data_path):
    plain_file.plain_file_parser("normal_requires_main.plain", [get_test_data_path("data/requires")])
