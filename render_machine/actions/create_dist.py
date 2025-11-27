from typing import Any

import file_utils
from plain2code_console import console
from render_machine.actions.base_action import BaseAction
from render_machine.render_context import RenderContext


class CreateDist(BaseAction):
    SUCCESSFUL_OUTCOME = "dist_created"

    def execute(self, render_context: RenderContext, _previous_action_payload: Any | None):
        # Copy build and conformance tests folders to output folders if specified
        if render_context.args.copy_build:
            file_utils.copy_folder_to_output(
                render_context.args.build_folder,
                render_context.args.build_dest,
            )
        if render_context.args.copy_conformance_tests:
            file_utils.copy_folder_to_output(
                render_context.args.conformance_tests_folder,
                render_context.args.conformance_tests_dest,
            )
        console.info(f"Render {render_context.run_state.render_id} completed successfully.")

        return self.SUCCESSFUL_OUTCOME, None
