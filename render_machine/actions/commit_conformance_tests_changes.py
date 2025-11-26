from typing import Any

import git_utils
import plain_spec
from render_machine.actions.base_action import BaseAction
from render_machine.render_context import RenderContext


class CommitConformanceTestsChanges(BaseAction):
    SUCCESSFUL_OUTCOME_IMPLEMENTATION_NOT_UPDATED = "conformance_tests_changes_committed_implementation_not_updated"
    SUCCESSFUL_OUTCOME_IMPLEMENTATION_UPDATED = "conformance_tests_changes_committed_implementation_updated"

    def __init__(self, implementation_code_commit_message: str, conformance_tests_commit_message: str):
        self.implementation_code_commit_message = implementation_code_commit_message
        self.conformance_tests_commit_message = conformance_tests_commit_message

    def execute(self, render_context: RenderContext, _previous_action_payload: Any | None):
        implementation_updated = False
        if git_utils.is_dirty(render_context.args.build_folder):
            git_utils.add_all_files_and_commit(
                render_context.args.build_folder,
                self.implementation_code_commit_message,
                render_context.frid_context.frid,
                render_context.run_state.render_id,
            )
            implementation_updated = True
        functional_requirement_text = render_context.frid_context.specifications[plain_spec.FUNCTIONAL_REQUIREMENTS][-1]
        templated_functional_requirement_finished_commit_msg = self.conformance_tests_commit_message.format(
            render_context.frid_context.frid
        )
        formatted_conformance_commit_msg = (
            f"{functional_requirement_text}\n\n{templated_functional_requirement_finished_commit_msg}"
        )
        render_context.conformance_tests_utils.dump_conformance_tests_json(
            render_context.conformance_tests_running_context.conformance_tests_json
        )
        git_utils.add_all_files_and_commit(
            render_context.args.conformance_tests_folder,
            formatted_conformance_commit_msg,
            None,
            render_context.run_state.render_id,
        )
        if implementation_updated:
            return self.SUCCESSFUL_OUTCOME_IMPLEMENTATION_UPDATED, None
        else:
            return self.SUCCESSFUL_OUTCOME_IMPLEMENTATION_NOT_UPDATED, None
