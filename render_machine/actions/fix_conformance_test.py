from typing import Any

import file_utils
import plain_spec
from plain2code_console import console
from plain2code_exceptions import UnexpectedState
from render_machine.actions.base_action import BaseAction
from render_machine.conformance_test_helpers import ConformanceTestHelpers
from render_machine.implementation_code_helpers import ImplementationCodeHelpers
from render_machine.render_context import RenderContext


class FixConformanceTest(BaseAction):
    IMPLEMENTATION_CODE_NOT_UPDATED = "implementation_code_not_updated"
    IMPLEMENTATION_CODE_UPDATED = "implementation_code_updated"

    def execute(self, render_context: RenderContext, previous_action_payload: Any | None):
        console.info(
            f"Fixing conformance test for functional requirement {render_context.conformance_tests_running_context.current_testing_frid}."
        )

        if not previous_action_payload.get("previous_conformance_tests_issue"):
            raise UnexpectedState("Previous action payload does not contain previous conformance tests issue.")
        previous_conformance_tests_issue = previous_action_payload["previous_conformance_tests_issue"]

        if render_context.conformance_tests_running_context.current_testing_frid == render_context.frid_context.frid:
            console_message = f"Fixing conformance test for functional requirement {render_context.conformance_tests_running_context.current_testing_frid}."
        else:
            console_message = f"While implementing functional requirement {render_context.frid_context.frid}, conformance tests for functional requirement {render_context.conformance_tests_running_context.current_testing_frid} broke. Fixing them..."

        existing_files, existing_files_content = ImplementationCodeHelpers.fetch_existing_files(render_context)
        (
            existing_conformance_test_files,
            existing_conformance_test_files_content,
        ) = ConformanceTestHelpers.fetch_existing_conformance_test_files(
            render_context.conformance_tests_running_context  # type: ignore
        )
        previous_frid_code_diff = ImplementationCodeHelpers.get_code_diff(render_context)

        if render_context.args.verbose:
            tmp_resources_list = []
            plain_spec.collect_linked_resources(
                render_context.plain_source_tree,
                tmp_resources_list,
                None,
                False,
                render_context.frid_context.frid,
            )
            console.print_resources(tmp_resources_list, render_context.frid_context.linked_resources)

            console.print_files(
                "Implementation files sent as input for fixing conformance tests issues:",
                render_context.args.build_folder,
                existing_files_content,
                style=console.INPUT_STYLE,
            )

            console.print_files(
                "Conformance tests files sent as input for fixing conformance tests issues:",
                ConformanceTestHelpers.get_current_conformance_test_folder_name(
                    render_context.conformance_tests_running_context  # type: ignore
                ),
                existing_conformance_test_files_content,
                style=console.INPUT_STYLE,
            )

        acceptance_tests = ConformanceTestHelpers.get_current_acceptance_tests(
            render_context.conformance_tests_running_context  # type: ignore
        )
        conformance_tests_folder_name = ConformanceTestHelpers.get_current_conformance_test_folder_name(
            render_context.conformance_tests_running_context  # type: ignore
        )
        with console.status(console_message):
            [conformance_tests_fixed, response_files] = render_context.codeplain_api.fix_conformance_tests_issue(
                render_context.frid_context.frid,
                render_context.conformance_tests_running_context.current_testing_frid,
                render_context.plain_source_tree,
                render_context.frid_context.linked_resources,
                existing_files_content,
                previous_frid_code_diff,
                existing_conformance_test_files_content,
                acceptance_tests,
                previous_conformance_tests_issue,
                render_context.conformance_tests_running_context.fix_attempts,
                conformance_tests_folder_name,
                render_context.conformance_tests_running_context.current_testing_frid_high_level_implementation_plan,
                render_context.run_state,
            )

        if conformance_tests_fixed:
            file_utils.store_response_files(
                ConformanceTestHelpers.get_current_conformance_test_folder_name(
                    render_context.conformance_tests_running_context  # type: ignore
                ),
                response_files,
                existing_conformance_test_files,
            )
            if render_context.args.verbose:
                console.print_files(
                    "Conformance test files fixed:",
                    ConformanceTestHelpers.get_current_conformance_test_folder_name(
                        render_context.conformance_tests_running_context  # type: ignore
                    ),
                    response_files,
                    style=console.OUTPUT_STYLE,
                )
            return self.IMPLEMENTATION_CODE_NOT_UPDATED, None
        else:
            if len(response_files) > 0:
                file_utils.store_response_files(render_context.args.build_folder, response_files, existing_files)
                if render_context.args.verbose:
                    console.print_files(
                        "Files fixed:",
                        render_context.args.build_folder,
                        response_files,
                        style=console.OUTPUT_STYLE,
                    )
                render_context.conformance_tests_running_context.should_prepare_testing_environment = True
                return self.IMPLEMENTATION_CODE_UPDATED, None
            else:
                return self.IMPLEMENTATION_CODE_NOT_UPDATED, None
