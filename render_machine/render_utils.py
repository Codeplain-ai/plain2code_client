import subprocess
import tempfile
import time

import file_utils
import git_utils
import plain_spec
from plain2code_console import console

TEST_SCRIPT_EXECUTION_TIMEOUT = 120
TIMEOUT_ERROR_EXIT_CODE = 124


def revert_uncommitted_changes(render_context):
    if render_context.frid_context.frid is not None:
        previous_frid = plain_spec.get_previous_frid(render_context.plain_source_tree, render_context.frid_context.frid)
        git_utils.revert_to_commit_with_frid(render_context.args.build_folder, previous_frid)


def print_inputs(render_context, existing_files_content, message):
    tmp_resources_list = []
    plain_spec.collect_linked_resources(
        render_context.plain_source_tree,
        tmp_resources_list,
        [
            plain_spec.DEFINITIONS,
            plain_spec.NON_FUNCTIONAL_REQUIREMENTS,
            plain_spec.FUNCTIONAL_REQUIREMENTS,
        ],
        False,
        render_context.frid_context.frid,
    )
    console.print_resources(tmp_resources_list, render_context.frid_context.linked_resources)

    console.print_files(
        message,
        render_context.args.build_folder,
        existing_files_content,
        style=console.INPUT_STYLE,
    )


def execute_test_script(test_script, scripts_args, verbose, test_type):
    try:
        start_time = time.time()
        result = subprocess.run(
            [file_utils.add_current_path_if_no_path(test_script)] + scripts_args,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=TEST_SCRIPT_EXECUTION_TIMEOUT,
        )
        elapsed_time = time.time() - start_time
        # Log the info about the tests
        if verbose:
            with tempfile.NamedTemporaryFile(mode="w+", delete=False, suffix=".test_output") as temp_file:
                temp_file.write("\n═════════════════════════ Test Script Output ═════════════════════════\n")
                temp_file.write(result.stdout)
                temp_file.write("\n══════════════════════════════════════════════════════════════════════\n")
                temp_file_path = temp_file.name
                if result.returncode != 0:
                    temp_file.write(f"Test script {test_script} failed with exit code {result.returncode}.\n")
                else:
                    temp_file.write(f"Test script {test_script} successfully passed.\n")
                temp_file.write(f"Test execution time: {elapsed_time:.2f} seconds.\n")

            console.info(f"[b]Test output stored in: {temp_file_path}[/b]")

            if result.returncode != 0:
                console.info(
                    f"[b]The {test_type} tests have failed. Initiating the patching mode to automatically correct the discrepancies.[/b]\n"
                )
            else:
                console.info(f"[b]All {test_type} tests passed successfully.[/b]\n")

        return result.returncode, result.stdout
    except subprocess.TimeoutExpired as e:
        # Store timeout output in a temporary file
        if verbose:
            with tempfile.NamedTemporaryFile(mode="w+", delete=False, suffix=".test_timeout") as temp_file:
                temp_file.write(f"Test script {test_script} timed out after {TEST_SCRIPT_EXECUTION_TIMEOUT} seconds.")
                if e.stdout:
                    decoded_output = e.stdout.decode("utf-8") if isinstance(e.stdout, bytes) else e.stdout
                    temp_file.write(f"Test script partial output before the timeout:\n{decoded_output}")
                else:
                    temp_file.write("Test script did not produce any output before the timeout.")
                temp_file_path = temp_file.name
            console.warning(
                f"The {test_type} test timed out after {TEST_SCRIPT_EXECUTION_TIMEOUT} seconds. Test output stored in: {temp_file_path}\n"
            )

        return TIMEOUT_ERROR_EXIT_CODE, f"Tests did not finish in {TEST_SCRIPT_EXECUTION_TIMEOUT} seconds."
