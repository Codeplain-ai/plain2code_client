from typing import Any

import render_machine.render_utils as render_utils
from plain2code_console import console
from render_machine.actions.base_action import BaseAction
from render_machine.conformance_test_helpers import ConformanceTestHelpers
from render_machine.render_context import RenderContext

UNRECOVERABLE_ERROR_EXIT_CODES = [69]


class RunConformanceTests(BaseAction):

    SUCCESSFUL_OUTCOME = "conformance_tests_passed"
    FAILED_OUTCOME = "conformance_tests_failed"
    UNRECOVERABLE_ERROR_OUTCOME = "unrecoverable_error_occurred"

    def execute(self, render_context: RenderContext, _previous_action_payload: Any | None):
        conformance_tests_folder_name = ConformanceTestHelpers.get_current_conformance_test_folder_name(
            render_context.conformance_tests_running_context  # type: ignore
        )

        if render_context.args.verbose:
            console.info(
                f"\n[b]Running conformance tests script {render_context.args.conformance_tests_script} for {conformance_tests_folder_name} (functional requirement {render_context.conformance_tests_running_context.current_testing_frid}).[/b]"
            )
        exit_code, conformance_tests_issue = render_utils.execute_script(
            render_context.args.conformance_tests_script,
            [render_context.args.build_folder, conformance_tests_folder_name],
            render_context.args.verbose,
            "Conformance Tests",
        )

        if exit_code == 0:
            return self.SUCCESSFUL_OUTCOME, None

        if exit_code in UNRECOVERABLE_ERROR_EXIT_CODES:
            console.error(conformance_tests_issue)
            return (
                self.UNRECOVERABLE_ERROR_OUTCOME,
                {"previous_conformance_tests_issue": conformance_tests_issue},
            )

        return self.FAILED_OUTCOME, {"previous_conformance_tests_issue": conformance_tests_issue}
