from typing import Any

import render_machine.render_utils as render_utils
from plain2code_console import console
from render_machine.actions.base_action import BaseAction
from render_machine.render_context import RenderContext

UNRECOVERABLE_ERROR_EXIT_CODES = [69]


class RunUnitTests(BaseAction):
    SUCCESSFUL_OUTCOME = "unit_tests_succeeded"
    FAILED_OUTCOME = "unit_tests_failed"
    UNRECOVERABLE_ERROR_OUTCOME = "unrecoverable_error_occurred"

    def execute(self, render_context: RenderContext, _previous_action_payload: Any | None):
        if render_context.args.verbose:
            console.info(
                f"[b]Running unit tests script {render_context.args.unittests_script}.[/b] (attempt: {render_context.unit_tests_running_context.fix_attempts + 1})"
            )
        exit_code, unittests_issue = render_utils.execute_script(
            render_context.args.unittests_script,
            [render_context.args.build_folder],
            render_context.args.verbose,
            "Unit Tests",
        )

        if exit_code == 0:
            return self.SUCCESSFUL_OUTCOME, None

        elif exit_code in UNRECOVERABLE_ERROR_EXIT_CODES:
            console.error(unittests_issue)
            return (
                self.UNRECOVERABLE_ERROR_OUTCOME,
                "Unit tests script failed due to problems in the environment setup. Please check the your environment or update the script for running unittests.",
            )
        else:
            return self.FAILED_OUTCOME, {"previous_unittests_issue": unittests_issue}
