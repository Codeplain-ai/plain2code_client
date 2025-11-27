import os
from typing import Optional

import file_utils
import plain_spec
from render_machine.render_types import ConformanceTestsRunningContext


class ConformanceTestHelpers:
    @staticmethod
    def fetch_existing_conformance_test_folder_names(conformance_tests_folder: str):
        if os.path.isdir(conformance_tests_folder):
            existing_folder_names = file_utils.list_folders_in_directory(conformance_tests_folder)
        else:
            # This happens if we're rendering the first FRID (without previously created conformance tests)
            existing_folder_names = []
        return existing_folder_names

    @staticmethod
    def fetch_existing_conformance_test_files(conformance_tests_running_context: ConformanceTestsRunningContext):
        conformance_test_folder_name = ConformanceTestHelpers.get_current_conformance_test_folder_name(
            conformance_tests_running_context
        )
        existing_conformance_test_files = file_utils.list_all_text_files(conformance_test_folder_name)
        existing_conformance_test_files_content = file_utils.get_existing_files_content(
            conformance_test_folder_name, existing_conformance_test_files
        )
        return existing_conformance_test_files, existing_conformance_test_files_content

    @staticmethod
    def current_conformance_tests_exist(conformance_tests_running_context: ConformanceTestsRunningContext) -> bool:
        return (
            conformance_tests_running_context.conformance_tests_json.get(
                conformance_tests_running_context.current_testing_frid
            )
            is not None
        )

    @staticmethod
    def get_current_conformance_test_folder_name(
        conformance_tests_running_context: ConformanceTestsRunningContext,
    ) -> str:
        return conformance_tests_running_context.conformance_tests_json[
            conformance_tests_running_context.current_testing_frid
        ]["folder_name"]

    @staticmethod
    def get_current_acceptance_tests(
        conformance_tests_running_context: ConformanceTestsRunningContext,
    ) -> Optional[list[str]]:
        if (
            plain_spec.ACCEPTANCE_TESTS
            in conformance_tests_running_context.conformance_tests_json[
                conformance_tests_running_context.current_testing_frid
            ]
        ):
            return conformance_tests_running_context.conformance_tests_json[
                conformance_tests_running_context.current_testing_frid
            ][plain_spec.ACCEPTANCE_TESTS]
        return None

    @staticmethod
    def set_current_conformance_tests_summary(
        conformance_tests_running_context: ConformanceTestsRunningContext, summary: list[dict]
    ):
        conformance_tests_running_context.conformance_tests_json[
            conformance_tests_running_context.current_testing_frid
        ]["test_summary"] = summary
