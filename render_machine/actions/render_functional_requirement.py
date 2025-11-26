from typing import Any

import file_utils
import render_machine.render_utils as render_utils
from plain2code_console import console
from plain2code_exceptions import FunctionalRequirementTooComplex
from render_machine.actions.base_action import BaseAction
from render_machine.implementation_code_helpers import ImplementationCodeHelpers
from render_machine.render_context import RenderContext

MAX_CODE_GENERATION_RETRIES = 2


class RenderFunctionalRequirement(BaseAction):
    SUCCESSFUL_OUTCOME = "code_and_unit_tests_generated"
    FUNCTIONAL_REQUIREMENT_TOO_COMPLEX_OUTCOME = "functional_requirement_too_complex"

    def execute(self, render_context: RenderContext, _previous_action_payload: Any | None):
        render_utils.revert_uncommitted_changes(render_context)
        existing_files, existing_files_content = ImplementationCodeHelpers.fetch_existing_files(render_context)

        if render_context.args.verbose:
            msg = f"Rendering functional requirement {render_context.frid_context.frid}"
            if render_context.frid_context.functional_requirement_render_attempts > 1:
                msg += f", attempt number {render_context.frid_context.functional_requirement_render_attempts}/{MAX_CODE_GENERATION_RETRIES}."
            msg += f"\n[b]{render_context.frid_context.functional_requirement_text}[/b]"
            console.info("\n-------------------------------------")
            console.info(msg)
            console.info("-------------------------------------\n")

        try:
            if render_context.args.verbose:
                render_utils.print_inputs(
                    render_context, existing_files_content, "Files sent as input to code generation:"
                )

            with console.status(
                f"[{console.INFO_STYLE}]Generating functional requirement {render_context.frid_context.frid}...\n"
            ):
                response_files = render_context.codeplain_api.render_functional_requirement(
                    render_context.frid_context.frid,
                    render_context.plain_source_tree,
                    render_context.frid_context.linked_resources,
                    existing_files_content,
                    render_context.run_state,
                )
        except FunctionalRequirementTooComplex as e:
            error_message = f"The functional requirement:\n[b]{render_context.frid_context.functional_requirement_text}[/b]\n is too complex to be implemented. Please break down the functional requirement into smaller parts ({str(e)})."
            if e.proposed_breakdown:
                error_message += "\nProposed breakdown:"
                for _, part in e.proposed_breakdown.items():
                    error_message += f"\n  - {part}"

            return self.FUNCTIONAL_REQUIREMENT_TOO_COMPLEX_OUTCOME, error_message

        _, changed_files = file_utils.update_build_folder_with_rendered_files(
            render_context.args.build_folder, existing_files, response_files
        )
        render_context.frid_context.changed_files.update(changed_files)

        if render_context.args.verbose:
            console.print_files(
                "Files generated or updated:",
                render_context.args.build_folder,
                response_files,
                style=console.OUTPUT_STYLE,
            )

        return self.SUCCESSFUL_OUTCOME, None
