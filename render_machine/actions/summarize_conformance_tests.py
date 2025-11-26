from typing import Any

from plain2code_console import console
from render_machine.actions.base_action import BaseAction
from render_machine.conformance_test_helpers import ConformanceTestHelpers
from render_machine.render_context import RenderContext


class SummarizeConformanceTests(BaseAction):
    SUCCESSFUL_OUTCOME = "conformance_tests_summarized"

    def execute(self, render_context: RenderContext, _previous_action_payload: Any | None):
        console.info(f"Summarizing conformance tests for functional requirement {render_context.frid_context.frid}.")

        _, existing_conformance_test_files_content = ConformanceTestHelpers.fetch_existing_conformance_test_files(
            render_context.conformance_tests_running_context  # type: ignore
        )

        with console.status(
            f"[{console.INFO_STYLE}]Summarizing finished conformance tests for functional requirement {render_context.frid_context.frid}...\n"
        ):
            summary = render_context.codeplain_api.summarize_finished_conformance_tests(
                frid=render_context.frid_context.frid,
                plain_source_tree=render_context.plain_source_tree,
                linked_resources=render_context.frid_context.linked_resources,
                conformance_test_files_content=existing_conformance_test_files_content,
                run_state=render_context.run_state,
            )

        ConformanceTestHelpers.set_current_conformance_tests_summary(
            render_context.conformance_tests_running_context, summary  # type: ignore
        )

        return self.SUCCESSFUL_OUTCOME, None
