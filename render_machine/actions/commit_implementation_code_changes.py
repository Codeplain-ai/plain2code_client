from typing import Any

import git_utils
from render_machine.actions.base_action import BaseAction
from render_machine.render_context import RenderContext


class CommitImplementationCodeChanges(BaseAction):
    SUCCESSFUL_OUTCOME = "implementation_code_changes_committed"

    def __init__(self, base_commit_message: str):
        self.base_commit_message = base_commit_message

    def execute(self, render_context: RenderContext, _previous_action_payload: Any | None):
        git_utils.add_all_files_and_commit(
            render_context.args.build_folder,
            self.base_commit_message.format(render_context.frid_context.frid),
            render_context.frid_context.frid,
            render_context.run_state.render_id,
        )

        return self.SUCCESSFUL_OUTCOME, None
