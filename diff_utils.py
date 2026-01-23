from difflib import unified_diff


def get_unified_diff(filename: str, existing_file_content: str, response_file_content: str) -> str:
    diff = unified_diff(
        existing_file_content.splitlines(keepends=True),
        response_file_content.splitlines(keepends=True),
        fromfile=filename,
        tofile=filename,
    )

    return "".join(diff)


def get_code_diff(response_files: dict[str, str], existing_files_content: dict[str, str]) -> dict[str, str]:
    code_diff: dict[str, str] = {}
    for file_name in response_files:
        if file_name in existing_files_content and existing_files_content[file_name]:
            if response_files[file_name]:
                unified_diff_result = get_unified_diff(
                    file_name,
                    existing_files_content[file_name],
                    response_files[file_name],
                )
                if unified_diff_result and unified_diff_result.strip():
                    code_diff[file_name] = unified_diff_result
            else:
                code_diff[file_name] = f"File {file_name} was deleted."
        else:
            code_diff[file_name] = response_files[file_name]

    return code_diff
