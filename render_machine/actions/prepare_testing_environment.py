from typing import Any

import render_machine.render_utils as render_utils
from plain2code_console import console
from render_machine.actions.base_action import BaseAction
from render_machine.render_context import RenderContext


class PrepareTestingEnvironment(BaseAction):
    SUCCESSFUL_OUTCOME = "testing_environment_prepared"
    FAILED_OUTCOME = "testing_environment_preparation_failed"

    def execute(self, render_context: RenderContext, _previous_action_payload: Any | None):
        if render_context.args.verbose:
            console.info(
                f"[b]Running testing environment preparation script {render_context.args.prepare_environment_script} for build folder {render_context.args.build_folder}.[/b]"
            )
        exit_code, _ = render_utils.execute_script(
            render_context.args.prepare_environment_script,
            [render_context.args.build_folder],
            render_context.args.verbose,
            "Testing Environment Preparation",
        )

        render_context.conformance_tests_running_context.should_prepare_testing_environment = False

        if exit_code == 0:
            return self.SUCCESSFUL_OUTCOME, None
        else:
            return self.FAILED_OUTCOME, None
