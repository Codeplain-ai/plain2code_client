import json

import file_utils
import git_utils
import plain_spec


class ImplementationCodeHelpers:
    @staticmethod
    def calculate_build_folder_hash(build_folder: str) -> str:
        _, existing_files_content = ImplementationCodeHelpers.fetch_existing_files(build_folder)
        return plain_spec.hash_text(f"folder={build_folder}|{json.dumps(existing_files_content)}")

    @staticmethod
    def fetch_existing_files(build_folder: str):
        existing_files = file_utils.list_all_text_files(build_folder)
        existing_files_content = file_utils.get_existing_files_content(build_folder, existing_files)
        return existing_files, existing_files_content

    @staticmethod
    def get_code_diff(build_folder: str, plain_source_tree: dict, frid: str):
        previous_frid_code_diff = git_utils.diff(
            build_folder,
            plain_spec.get_previous_frid(plain_source_tree, frid),
        )
        return previous_frid_code_diff
