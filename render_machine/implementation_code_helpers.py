import file_utils
import git_utils
import plain_spec
from render_machine.render_context import RenderContext


class ImplementationCodeHelpers:
    @staticmethod
    def fetch_existing_files(render_context: RenderContext):
        existing_files = file_utils.list_all_text_files(render_context.args.build_folder)
        existing_files_content = file_utils.get_existing_files_content(render_context.args.build_folder, existing_files)
        return existing_files, existing_files_content

    @staticmethod
    def get_code_diff(render_context: RenderContext):
        previous_frid_code_diff = git_utils.diff(
            render_context.args.build_folder,
            plain_spec.get_previous_frid(render_context.plain_source_tree, render_context.frid_context.frid),
        )
        return previous_frid_code_diff
