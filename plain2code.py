import importlib.util
import logging
import logging.config
import os
import subprocess
import sys
import tempfile
import traceback

import yaml
from liquid2.exceptions import TemplateNotFoundError

import file_utils
import git_utils
import plain_spec
from codeplain_REST_api import CodeplainAPI
from plain2code_arguments import parse_arguments
from plain2code_console import console
from plain2code_state import (
    CONFORMANCE_TESTS_BACKUP_FOLDER_SUFFIX,
    CONFORMANCE_TESTS_DEFINITION_FILE_NAME,
    ConformanceTestsState,
    ExecutionState,
    RunState,
)
from system_config import system_config

TEST_SCRIPT_EXECUTION_TIMEOUT = 120  # 120 seconds
LOGGING_CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logging_config.yaml")

DEFAULT_TEMPLATE_DIRS = "standard_template_library"

MAX_UNITTEST_FIX_ATTEMPTS = 10
MAX_CONFORMANCE_TEST_FIX_ATTEMPTS = 10
MAX_CONFORMANCE_TEST_RUNS = 10
MAX_REFACTORING_ITERATIONS = 5
MAX_UNIT_TEST_RENDER_RETRIES = 2


class InvalidFridArgument(Exception):
    pass


def get_render_range(render_range, plain_source_tree):
    render_range = render_range.split(",")
    range_end = render_range[1] if len(render_range) == 2 else render_range[0]

    return _get_frids_range(plain_source_tree, render_range[0], range_end)


def get_render_range_from(start, plain_source_tree):
    return _get_frids_range(plain_source_tree, start)


def _get_frids_range(plain_source_tree, start, end=None):
    frids = list(plain_spec.get_frids(plain_source_tree))

    if start not in frids:
        raise InvalidFridArgument(f"Invalid start functional requirement ID: {start}. Valid IDs are: {frids}.")

    if end is not None:
        if end not in frids:
            raise InvalidFridArgument(f"Invalid end functional requirement ID: {end}. Valid IDs are: {frids}.")

        end_idx = frids.index(end) + 1
    else:
        end_idx = len(frids)

    start_idx = frids.index(start)
    if start_idx >= end_idx:
        raise InvalidFridArgument(
            f"Start functional requirement ID: {start} must be before end functional requirement ID: {end}."
        )

    return frids[start_idx:end_idx]


def execute_test_script(test_script, scripts_args, verbose, test_type):
    try:
        result = subprocess.run(
            [file_utils.add_current_path_if_no_path(test_script)] + scripts_args,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=TEST_SCRIPT_EXECUTION_TIMEOUT,
        )

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

            console.info(f"[b]Test output stored in: {temp_file_path}[/b]")

            if result.returncode != 0:
                console.info(
                    f"[b]The {test_type} tests have failed. Initiating the patching mode to automatically correct the discrepancies.[/b]\n"
                )
            else:
                console.info(f"[b]All {test_type} tests passed successfully.[/b]\n")

        # Return the output of the test script if it failed
        if result.returncode != 0:
            return result.stdout
        return None
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

        return f"Tests did not finish in {TEST_SCRIPT_EXECUTION_TIMEOUT} seconds."


def run_unittests(
    args, codeplainAPI, frid, plain_source_tree, linked_resources, existing_files, run_state: RunState
) -> tuple[list[str], set[str], bool]:
    changed_files = set()

    if not args.unittests_script:
        return existing_files, changed_files, True

    if args.verbose:
        console.info(f"\n[b]Running unit tests script:[/b] {args.unittests_script}")

    unit_test_run_count = 0
    while unit_test_run_count < MAX_UNITTEST_FIX_ATTEMPTS:
        unit_test_run_count += 1

        if args.verbose:
            console.info(f"Running unit tests attempt {unit_test_run_count}.")

        unittests_issue = execute_test_script(args.unittests_script, [args.build_folder], args.verbose, "unit")

        if not unittests_issue:
            return existing_files, changed_files, True

        existing_files_content = file_utils.get_existing_files_content(args.build_folder, existing_files)

        if args.verbose:
            tmp_resources_list = []
            plain_spec.collect_linked_resources(
                plain_source_tree,
                tmp_resources_list,
                [
                    plain_spec.DEFINITIONS,
                    plain_spec.NON_FUNCTIONAL_REQUIREMENTS,
                    plain_spec.FUNCTIONAL_REQUIREMENTS,
                ],
                False,
                frid,
            )
            console.print_resources(tmp_resources_list, linked_resources)

            console.print_files(
                "Files sent as input for fixing unit tests:",
                args.build_folder,
                existing_files_content,
                style=console.INPUT_STYLE,
            )

        with console.status(f"[{console.INFO_STYLE}]Fixing unit tests issue for functional requirement {frid}...\n"):
            response_files = codeplainAPI.fix_unittests_issue(
                frid, plain_source_tree, linked_resources, existing_files_content, unittests_issue, run_state
            )

        changed_files.update(response_files.keys())

        existing_files = file_utils.store_response_files(args.build_folder, response_files, existing_files)
        if args.verbose:
            console.print_files("Files fixed:", args.build_folder, response_files, style=console.OUTPUT_STYLE)

    return existing_files, changed_files, False


def generate_conformance_tests(
    args,
    codeplainAPI: CodeplainAPI,
    frid,
    functional_requirement_id,
    plain_source_tree,
    linked_resources,
    existing_files_content,
    conformance_tests_folder_name,
    run_state: RunState,
):
    specifications, _ = plain_spec.get_specifications_for_frid(plain_source_tree, functional_requirement_id)
    if args.verbose:
        console.info("\n[b]Implementing test requirements:[/b]")
        console.print_list(specifications[plain_spec.TEST_REQUIREMENTS], style=console.INFO_STYLE)
        console.info()

    if not conformance_tests_folder_name:
        try:
            existing_folder_names = file_utils.list_folders_in_directory(args.conformance_tests_folder)
        except FileNotFoundError:
            # This happens if we're rendering the first FRID (without previously created conformance tests)
            existing_folder_names = []

        with console.status(
            f"[{console.INFO_STYLE}]Generating folder name for conformance tests for functional requirement {frid}...\n"
        ):
            fr_subfolder_name = codeplainAPI.generate_folder_name_from_functional_requirement(
                frid=frid,
                functional_requirement=specifications[plain_spec.FUNCTIONAL_REQUIREMENTS][-1],
                existing_folder_names=existing_folder_names,
                run_state=run_state,
            )

        if args.verbose:
            console.info(f"Storing conformance test files in subfolder {fr_subfolder_name}")

        conformance_tests_folder_name = os.path.join(args.conformance_tests_folder, fr_subfolder_name)

    file_utils.delete_files_and_subfolders(conformance_tests_folder_name, args.debug)

    if args.verbose:
        tmp_resources_list = []
        plain_spec.collect_linked_resources(
            plain_source_tree,
            tmp_resources_list,
            [
                plain_spec.DEFINITIONS,
                plain_spec.TEST_REQUIREMENTS,
                plain_spec.FUNCTIONAL_REQUIREMENTS,
            ],
            False,
            frid,
        )
        console.print_resources(tmp_resources_list, linked_resources)

        console.print_files(
            "Files sent as input for generating conformance tests:",
            args.build_folder,
            existing_files_content,
            style=console.INPUT_STYLE,
        )

    with console.status(f"[{console.INFO_STYLE}]Generating conformance tests for functional requirement {frid}...\n"):
        response_files = codeplainAPI.render_conformance_tests(
            frid,
            functional_requirement_id,
            plain_source_tree,
            linked_resources,
            existing_files_content,
            run_state,
        )

    file_utils.store_response_files(conformance_tests_folder_name, response_files, [])

    if args.verbose:
        console.print_files(
            "Conformance test files generated:",
            conformance_tests_folder_name,
            response_files,
            style=console.OUTPUT_STYLE,
        )

    return {
        "functional_requirement": specifications[plain_spec.FUNCTIONAL_REQUIREMENTS][-1],
        "folder_name": conformance_tests_folder_name,
    }


def run_conformance_tests(  # noqa: C901
    args,
    codeplainAPI,
    frid,
    functional_requirement_id,
    plain_source_tree,
    linked_resources,
    existing_files,
    existing_files_content,
    code_diff,
    conformance_tests_folder_name,
    acceptance_tests,
    run_state: RunState,
) -> tuple[bool, bool, list[str], bool]:
    """
    Returns:
    (
        success,
        implementation_code_has_changed,
        existing_files,
        unittests_fixed_successfully,
    )
    Note that success may be misleading since:
    - If implementation_code_has_changed is True => success is True
    - If we're successful at patching conformance tests => success is True
    """
    conformance_test_fix_count = 0
    implementation_fix_count = 1
    conformance_tests_files = file_utils.list_all_text_files(conformance_tests_folder_name)
    while True:
        conformance_test_fix_count += 1

        if args.verbose:
            console.info(
                f"\n[b]Running conformance tests script {args.conformance_tests_script} for {conformance_tests_folder_name} (functional requirement {functional_requirement_id}, attempt: {conformance_test_fix_count}).[/b]"
            )

        conformance_tests_issue = execute_test_script(
            args.conformance_tests_script,
            [args.build_folder, conformance_tests_folder_name],
            args.verbose,
            "conformance",
        )

        if not conformance_tests_issue:
            break

        if conformance_test_fix_count > MAX_CONFORMANCE_TEST_FIX_ATTEMPTS:
            console.info(
                f"Conformance tests script {args.conformance_tests_script} for {conformance_tests_folder_name} still failed after {conformance_test_fix_count - 1} attempts at fixing issues."
            )
            return [False, False, existing_files, True]

        conformance_tests_files_content = file_utils.get_existing_files_content(
            conformance_tests_folder_name, conformance_tests_files
        )

        if args.verbose:
            tmp_resources_list = []
            plain_spec.collect_linked_resources(
                plain_source_tree,
                tmp_resources_list,
                None,
                False,
                frid,
            )
            console.print_resources(tmp_resources_list, linked_resources)

            console.print_files(
                "Implementation files sent as input for fixing conformance tests issues:",
                args.build_folder,
                existing_files_content,
                style=console.INPUT_STYLE,
            )

            console.print_files(
                "Conformance tests files sent as input for fixing conformance tests issues:",
                conformance_tests_folder_name,
                conformance_tests_files_content,
                style=console.INPUT_STYLE,
            )

        try:
            if frid == functional_requirement_id:
                console_message = f"Fixing conformance tests for functional requirement {frid}...\n"
            else:
                console_message = f"While implementing functional requirement {frid}, conformance tests for functional requirement {functional_requirement_id} broke. Fixing them...\n"
            with console.status(console_message):
                [conformance_tests_fixed, response_files] = codeplainAPI.fix_conformance_tests_issue(
                    frid,
                    functional_requirement_id,
                    plain_source_tree,
                    linked_resources,
                    existing_files_content,
                    code_diff,
                    conformance_tests_files_content,
                    acceptance_tests,
                    conformance_tests_issue,
                    implementation_fix_count,
                    run_state,
                )

            if conformance_tests_fixed:
                conformance_tests_files = file_utils.store_response_files(
                    conformance_tests_folder_name, response_files, conformance_tests_files
                )
                if args.verbose:
                    console.print_files(
                        f"Conformance test files in folder {conformance_tests_folder_name} fixed:",
                        conformance_tests_folder_name,
                        response_files,
                        style=console.OUTPUT_STYLE,
                    )

                implementation_fix_count = 1
            else:
                if len(response_files) > 0:
                    existing_files = file_utils.store_response_files(args.build_folder, response_files, existing_files)
                    if args.verbose:
                        console.print_files(
                            "Files fixed:", args.build_folder, response_files, style=console.OUTPUT_STYLE
                        )

                    [existing_files, _, unittests_success] = run_unittests(
                        args, codeplainAPI, frid, plain_source_tree, linked_resources, existing_files, run_state
                    )

                    if not unittests_success:
                        console.info(
                            f"Unsuccessful at patching unit tests after updating conformance tests for functional requirement {functional_requirement_id}."
                        )
                        return [False, False, existing_files, False]

                    # NOTE: At this point we're not running the conformance tests again.
                    # However, conformance tests are ran again within this rendering this functional requirement.
                    # Method `conformance_testing` then throws an exception if we return implementation_code_has_changed=True every time.
                    return [True, True, existing_files, True]

                console.info(
                    f"Couldn't fix conformance tests issue in folder {conformance_tests_folder_name} for functional requirement {functional_requirement_id}. Trying one more time."
                )
                implementation_fix_count += 1
        except codeplain_api.ConflictingRequirements as e:
            exit_with_error(f"Conflicting requirements. {str(e)}.", frid, run_state.render_id)
        except Exception as e:
            exit_with_error(f"Error fixing conformance tests issue: {str(e)}", frid, run_state.render_id)

    return [True, False, existing_files, True]


def generate_acceptance_test(
    codeplainAPI,
    frid,
    plain_source_tree,
    linked_resources,
    existing_files_content,
    conformance_tests_folder_name,
    acceptance_test,
    run_state: RunState,
):
    conformance_tests_files = file_utils.list_all_text_files(conformance_tests_folder_name)
    conformance_tests_files_content = file_utils.get_existing_files_content(
        conformance_tests_folder_name, conformance_tests_files
    )

    with console.status(f"[{console.INFO_STYLE}]Generating acceptance test for functional requirement {frid}...\n"):
        response_files = codeplainAPI.render_acceptance_tests(
            frid,
            plain_source_tree,
            linked_resources,
            existing_files_content,
            conformance_tests_files_content,
            acceptance_test,
            run_state,
        )

    conformance_tests_files = file_utils.store_response_files(
        conformance_tests_folder_name, response_files, conformance_tests_files
    )
    console.print_files(
        f"Conformance test files in folder {conformance_tests_folder_name} updated:",
        conformance_tests_folder_name,
        response_files,
        style=console.OUTPUT_STYLE,
    )


def conformance_testing(
    codeplainAPI,
    frid,
    plain_source_tree,
    linked_resources,
    conformance_tests,
    specifications,
    existing_files,
    existing_files_content,
    code_diff,
    run_state: RunState,
) -> tuple[bool, bool, bool, str]:
    """
    Returns: (success, implementation_code_has_changed, unittests_fixed_successfully, unsuccessfull_functional_requirement_id)
    """
    implementation_code_has_changed = False
    functional_requirement_id = plain_spec.get_first_frid(plain_source_tree)
    while functional_requirement_id is not None and not implementation_code_has_changed:
        if (functional_requirement_id == frid) and (
            frid not in conformance_tests
            or conformance_tests[frid]["functional_requirement"]
            != specifications[plain_spec.FUNCTIONAL_REQUIREMENTS][-1]
        ):
            if frid in conformance_tests:
                conformance_tests_folder_name = conformance_tests[frid]["folder_name"]
            else:
                conformance_tests_folder_name = None

            conformance_tests[frid] = generate_conformance_tests(
                args,
                codeplainAPI,
                frid,
                frid,
                plain_source_tree,
                linked_resources,
                existing_files_content,
                conformance_tests_folder_name,
                run_state,
            )

        conformance_tests_folder_name = conformance_tests[functional_requirement_id]["folder_name"]
        acceptance_tests = None
        if plain_spec.ACCEPTANCE_TESTS in conformance_tests[functional_requirement_id]:
            acceptance_tests = conformance_tests[functional_requirement_id][plain_spec.ACCEPTANCE_TESTS]

        [success, implementation_code_has_changed, existing_files, unittests_fixed_successfully] = (
            run_conformance_tests(
                args,
                codeplainAPI,
                frid,
                functional_requirement_id,
                plain_source_tree,
                linked_resources,
                existing_files,
                existing_files_content,
                code_diff,
                conformance_tests_folder_name,
                acceptance_tests,
                run_state,
            )
        )

        if functional_requirement_id == frid or not success or not unittests_fixed_successfully:
            return [
                success,
                implementation_code_has_changed,
                unittests_fixed_successfully,
                functional_requirement_id,
            ]

        functional_requirement_id = plain_spec.get_next_frid(plain_source_tree, functional_requirement_id)

    return [True, implementation_code_has_changed, True, functional_requirement_id]


def conformance_and_acceptance_testing(  # noqa: C901
    args,
    codeplainAPI,
    frid,
    plain_source_tree,
    linked_resources,
    existing_files,
    conformance_tests,
    run_state: RunState,
) -> tuple[any, bool]:
    """
    Returns: (conformance_tests, should_rerender_functional_requirement)
    At the moment, should_rerender_functional_requirement is exact opposite of unittest_fixed_successfully.
    """
    recreated_conformance_tests = False
    conformance_tests_run_count = 0
    acceptance_test_count = 0
    specifications, _ = plain_spec.get_specifications_for_frid(plain_source_tree, frid)
    while conformance_tests_run_count < MAX_CONFORMANCE_TEST_RUNS:
        conformance_tests_run_count += 1
        existing_files_content = file_utils.get_existing_files_content(args.build_folder, existing_files)

        if args.verbose:
            console.info(f"Running conformance tests attempt {conformance_tests_run_count}.")

        if frid == plain_spec.get_first_frid(plain_source_tree):
            code_diff = git_utils.diff(args.build_folder)
        else:
            # full diff between the previous frid and the current frid (including refactoring commits)
            code_diff = git_utils.diff(args.build_folder, plain_spec.get_previous_frid(plain_source_tree, frid))

        [
            success,
            implementation_code_has_changed,
            unittests_fixed_successfully,
            last_functional_requirement_id,
        ] = conformance_testing(
            codeplainAPI,
            frid,
            plain_source_tree,
            linked_resources,
            conformance_tests,
            specifications,
            existing_files,
            existing_files_content,
            code_diff,
            run_state,
        )

        """
        The flow in the rest of this method handles several key decision points:
        - If `unittests_fixed_successfully` is False: Return immediately, indicating the FR should be rerendered.
        - If `success` is True (initial conformance tests pass):
          - If `implementation_code_has_changed` is True: Continue to next outer loop iteration to rerun with updated code.
          - Otherwise: Process acceptance tests in sequence using a while loop that iterates through all acceptance tests or
            stops when a test fails or code changes:
              - Generate an acceptance test and add it to active tests
              - Run conformance tests with all acceptance tests processed so far
              - If tests succeed: Save the acceptance tests and continue unless code changed
              - If tests fail: Mark overall success as False, exit the acceptance tests loop
        - If any acceptance test or conformance test fails (`success` becomes False):
          - If tests were previously recreated: Exit with error
          - Otherwise: Recreate conformance tests from scratch and retry
        - When all acceptance tests are processed successfully without code changes:
          Return with successful status
        """

        if not unittests_fixed_successfully:
            return conformance_tests, True
        if success:
            if implementation_code_has_changed:
                continue

            # Initial FR conformance tests were successful. We reset the counter for the acceptance tests.
            conformance_tests_run_count = 0

            # Initial FR conformance run was successful and didn't change code.
            # Proceed to process acceptance tests if they exist and haven't all been processed yet.
            while (
                plain_spec.ACCEPTANCE_TESTS in specifications
                and acceptance_test_count < len(specifications[plain_spec.ACCEPTANCE_TESTS])
                and not implementation_code_has_changed
                and success
            ):
                acceptance_test = specifications[plain_spec.ACCEPTANCE_TESTS][acceptance_test_count]
                acceptance_test_count += 1

                if args.verbose:
                    console.info(f"Generating acceptance test #{acceptance_test_count}:\n{acceptance_test}")

                generate_acceptance_test(
                    codeplainAPI,
                    frid,
                    plain_source_tree,
                    linked_resources,
                    existing_files_content,
                    conformance_tests[frid]["folder_name"],
                    acceptance_test,
                    run_state,
                )

                generated_acceptance_tests = specifications[plain_spec.ACCEPTANCE_TESTS][:acceptance_test_count]

                # Run conformance tests including the newly generated acceptance test
                [
                    success,
                    implementation_code_has_changed,
                    existing_files,
                    unittests_fixed_successfully,
                ] = run_conformance_tests(
                    args,
                    codeplainAPI,
                    frid,
                    frid,
                    plain_source_tree,
                    linked_resources,
                    existing_files,
                    existing_files_content,
                    code_diff,
                    conformance_tests[frid]["folder_name"],
                    generated_acceptance_tests,
                    run_state,
                )

                if not unittests_fixed_successfully:
                    # No need to delete files and subfolders since we're doing that on the toplevel method render_functional_requirement
                    return conformance_tests, True

                if success:
                    conformance_tests[frid][plain_spec.ACCEPTANCE_TESTS] = generated_acceptance_tests

        if implementation_code_has_changed:
            continue

        if success:
            return conformance_tests, False

        if recreated_conformance_tests:
            exit_with_error(
                "We've already tried to fix the issue by recreating the conformance tests but tests still fail. Please fix the issues manually.",
                frid,
                run_state.render_id,
            )

        recreated_conformance_tests = True
        console.info("Recreating conformance tests.")

        conformance_tests_run_count = 0
        acceptance_test_count = 0

        conformance_tests[frid] = generate_conformance_tests(
            args,
            codeplainAPI,
            frid,
            last_functional_requirement_id,
            plain_source_tree,
            linked_resources,
            existing_files_content,
            conformance_tests[last_functional_requirement_id]["folder_name"],
            run_state,
        )

    exit_with_error(
        f"Conformance tests still failed after {conformance_tests_run_count} attempts at fixing issues. Please fix the issues manually.",
        frid,
        run_state.render_id,
    )


class IndentedFormatter(logging.Formatter):

    def format(self, record):
        original_message = record.getMessage()

        modified_message = original_message.replace("\n", "\n                ")

        record.msg = modified_message
        return super().format(record)


# TODO: Once we'll be refactoring and working with this method, we should also adjust cognitive complexity.
def render_functional_requirement(  # noqa: C901
    args,
    codeplainAPI: CodeplainAPI,
    plain_source_tree,
    frid,
    all_linked_resources,
    retry_state: ExecutionState,
    run_state: RunState,
):

    if args.render_range is not None:
        if frid not in args.render_range:
            if args.verbose:
                console.info("\n-------------------------------------")
                console.info(f"Skipping rendering iteration: {frid}")
                console.info("-------------------------------------\n")

            return
        else:
            previous_frid = plain_spec.get_previous_frid(plain_source_tree, frid)

            if frid == args.render_range[0] and previous_frid is not None and not args.dry_run:
                if args.verbose:
                    console.info(f"Checking out commit with frid {previous_frid}")

                git_utils.revert_to_commit_with_frid(args.build_folder, previous_frid)

    specifications, _ = plain_spec.get_specifications_for_frid(plain_source_tree, frid)

    is_first_frid = frid == plain_spec.get_first_frid(plain_source_tree)

    functional_requirement_text = specifications[plain_spec.FUNCTIONAL_REQUIREMENTS][-1]

    if args.verbose:
        console.info("\n-------------------------------------")
        console.info(f"Rendering functional requirement {frid}")
        console.info(f"[b]{functional_requirement_text}[/b]")
        console.info("-------------------------------------\n")

    if not args.dry_run and is_first_frid:
        if not os.path.isdir(args.build_folder):
            os.makedirs(args.build_folder)

            if args.debug:
                console.debug(f"Initializing a new git repository in build folder {args.build_folder}.")
        else:
            file_utils.delete_files_and_subfolders(args.build_folder)

        git_utils.init_clean_repo(args.build_folder)

    conformance_tests_state = ConformanceTestsState(
        conformance_tests_folder=args.conformance_tests_folder,
        backup_folder_suffix=CONFORMANCE_TESTS_BACKUP_FOLDER_SUFFIX,
        is_first_frid=is_first_frid,
        conformance_tests_definition_file_name=CONFORMANCE_TESTS_DEFINITION_FILE_NAME,
        conformance_tests_script=args.conformance_tests_script,
        verbose=args.verbose,
        debug=args.debug,
        dry_run=args.dry_run,
    )
    conformance_tests_state.init_backup_folder()

    if is_first_frid and not args.dry_run:
        if args.base_folder:
            file_utils.copy_folder_content(args.base_folder, args.build_folder)
            git_utils.add_all_files_and_commit(args.build_folder, git_utils.BASE_FOLDER_COMMIT_MESSAGE, None)

    resources_list = []
    plain_spec.collect_linked_resources(plain_source_tree, resources_list, None, True, frid)

    linked_resources = {}
    for resource in resources_list:
        linked_resources[resource["target"]] = all_linked_resources[resource["target"]]

    conformance_tests = conformance_tests_state.get_conformance_tests_json()

    if args.dry_run:
        if args.verbose:
            if plain_spec.ACCEPTANCE_TESTS in specifications:
                for i, acceptance_test in enumerate(specifications[plain_spec.ACCEPTANCE_TESTS], 1):
                    console.info(f"\nGenerating acceptance test #{i}:\n\n{acceptance_test}")

            console.warning("\n== Dry run: not actually rendering the functional requirement. ==\n")

        return

    functional_requirement_render_attempt = 0
    while True:
        existing_files = file_utils.list_all_text_files(args.build_folder)
        existing_files_content = file_utils.get_existing_files_content(args.build_folder, existing_files)

        functional_requirement_render_attempt += 1
        if args.verbose:
            if functional_requirement_render_attempt == 0:
                console.info(f"\nRendering functional requirement {frid}.")
            else:
                console.info(
                    f"\nRendering functional requirement {frid}, attempt number {functional_requirement_render_attempt}/{MAX_UNIT_TEST_RENDER_RETRIES}."
                )

        # Phase 1: Render the functional requirement.
        try:
            if args.verbose:

                tmp_resources_list = []
                plain_spec.collect_linked_resources(
                    plain_source_tree,
                    tmp_resources_list,
                    [
                        plain_spec.DEFINITIONS,
                        plain_spec.NON_FUNCTIONAL_REQUIREMENTS,
                        plain_spec.FUNCTIONAL_REQUIREMENTS,
                    ],
                    False,
                    frid,
                )
                console.print_resources(tmp_resources_list, linked_resources)

                console.print_files(
                    "Files sent as input to code generation:",
                    args.build_folder,
                    existing_files_content,
                    style=console.INPUT_STYLE,
                )

            with console.status(f"[{console.INFO_STYLE}]Generating functional requirement {frid}...\n"):
                response_files = codeplainAPI.render_functional_requirement(
                    frid, plain_source_tree, linked_resources, existing_files_content, run_state
                )
        except codeplain_api.FunctionalRequirementTooComplex as e:
            # TODO: Suggest how to break down the functional requirement. Identified options are:
            # - Split the functional requirement into smaller parts.
            # - If the functional requirement changes multiple entities, first limit the changes to a single representative entity and then to all entities.
            # - Move the functional requirement higher up, that is, to come earlier in the rendering order.
            error_message = f"The functional requirement:\n[b]{functional_requirement_text}[/b]\n is too complex to be implemented. Please break down the functional requirement into smaller parts ({str(e)})."
            if e.proposed_breakdown:
                error_message += "\nProposed breakdown:"
                for _, part in e.proposed_breakdown.items():
                    error_message += f"\n  - {part}"

            exit_with_error(
                error_message,
                frid,
                run_state.render_id,
            )

        existing_files, changed_files = file_utils.update_build_folder_with_rendered_files(
            args.build_folder, existing_files, response_files
        )
        if args.verbose:
            console.print_files(
                "Files generated or updated:", args.build_folder, response_files, style=console.OUTPUT_STYLE
            )

        # Phase 2: Run and patch unittests.
        console.info("\n[b]Running and patching unittests...[/b]")

        [existing_files, tmp_changed_files, unittest_success] = run_unittests(
            args,
            codeplainAPI,
            frid,
            plain_source_tree,
            linked_resources,
            existing_files,
            run_state,
        )

        if unittest_success:
            for file_name in tmp_changed_files:
                if file_name not in existing_files:
                    if file_name in changed_files:
                        changed_files.remove(file_name)
                else:
                    changed_files.add(file_name)

            git_utils.add_all_files_and_commit(args.build_folder, f"{functional_requirement_text}", frid)
            break

        # If unittests generation&patching failed for the first time => retry rendering functional requirement
        # If it failed for the second time => we're unable to fix the issue => exit with an error
        if functional_requirement_render_attempt < MAX_UNIT_TEST_RENDER_RETRIES:
            console.info(
                "Unittests could not be fixed after rendering the functional requirement. "
                f"Restarting rendering the functional requirement {frid} from scratch."
            )
            git_utils.revert_changes(args.build_folder)
            continue

        exit_with_error(
            f"Unittests could not be fixed after rendering the functional requirement {frid} for the {functional_requirement_render_attempt} time.",
            frid,
            run_state.render_id,
        )

    # Phase 3: Refactor the source code if needed.
    console.info("[b]Refactoring the generated code...[/b]")
    num_refactoring_iterations = 0
    while num_refactoring_iterations < MAX_REFACTORING_ITERATIONS:
        num_refactoring_iterations += 1
        if args.verbose:
            console.info(f"\nRefactoring iteration {num_refactoring_iterations}.")

        existing_files = file_utils.list_all_text_files(args.build_folder)
        existing_files_content = file_utils.get_existing_files_content(args.build_folder, existing_files)
        if args.verbose:
            console.print_files(
                "Files sent as input for refactoring:",
                args.build_folder,
                existing_files_content,
                style=console.INPUT_STYLE,
            )
        with console.status(
            f"[{console.INFO_STYLE}]Refactoring the generated code for functional requirement {frid}...\n"
        ):
            response_files = codeplainAPI.refactor_source_files_if_needed(
                frid=frid,
                files_to_check=changed_files,
                existing_files_content=existing_files_content,
                run_state=run_state,
            )

        if len(response_files) == 0:
            if args.verbose:
                console.info("No files refactored.")
            break

        existing_files = file_utils.store_response_files(args.build_folder, response_files, existing_files)
        if args.verbose:
            console.print_files("Files refactored:", args.build_folder, response_files, style=console.OUTPUT_STYLE)

        [existing_files, tmp_changed_files, unittest_success] = run_unittests(
            args,
            codeplainAPI,
            frid,
            plain_source_tree,
            linked_resources,
            existing_files,
            run_state,
        )

        if not unittest_success:
            if args.verbose:
                console.info(
                    f"Refactoring iteration {num_refactoring_iterations} was not successful for the functional requirement {frid}. "
                    f"Reverting to the previous valid state and retrying again."
                )
            git_utils.revert_changes(args.build_folder)
            continue

        for file_name in tmp_changed_files:
            if file_name not in existing_files:
                if file_name in changed_files:
                    changed_files.remove(file_name)
            else:
                changed_files.add(file_name)

        git_utils.add_all_files_and_commit(args.build_folder, f"Refactored code after implementing {frid}.", frid)

    # Phase 4: Conformance test the code.
    console.info("\n[b]Implementing conformance tests...[/b]\n")
    if (
        args.conformance_tests_script
        and (plain_spec.TEST_REQUIREMENTS in specifications or plain_spec.ACCEPTANCE_TESTS in specifications)
        and (specifications[plain_spec.TEST_REQUIREMENTS] or specifications[plain_spec.ACCEPTANCE_TESTS])
    ):
        conformance_tests, should_rerender_functional_requirement = conformance_and_acceptance_testing(
            args,
            codeplainAPI,
            frid,
            plain_source_tree,
            linked_resources,
            existing_files,
            conformance_tests,
            run_state,
        )

        if should_rerender_functional_requirement:
            # Restore the code state to initial
            git_utils.revert_changes(args.build_folder)
            # Restore the conformance tests state to initial
            conformance_tests_state.restore_from_backup()
            retry_state.mark_failed_conformance_testing_rendering()

            if retry_state.should_rerender_functional_requirement():
                if args.verbose:
                    console.info(
                        f"Unsuccessful at conformance testing (attempt {retry_state.conformance_testing_rendering_retries}/{retry_state.MAX_CONFORMANCE_TESTING_RENDERING_RETRIES}). "
                        f"Rerendering the functional requirement {frid} from scratch."
                    )
                return render_functional_requirement(
                    args, codeplainAPI, plain_source_tree, frid, all_linked_resources, retry_state, run_state
                )
            else:
                exit_with_error(
                    f"Unsuccessful at conformance testing after {retry_state.conformance_testing_rendering_retries}/{retry_state.MAX_CONFORMANCE_TESTING_RENDERING_RETRIES} attempts.",
                    frid,
                    run_state.render_id,
                )

        conformance_tests_state.dump_conformance_tests_json(conformance_tests)
        if git_utils.is_dirty(args.build_folder):
            git_utils.add_all_files_and_commit(
                args.build_folder,
                "Changes related to the conformance tests implementation.\nAll conformance tests passed.",
                frid,
            )

    return


def render(args, run_state: RunState):
    if args.verbose:
        # Try to load logging configuration from YAML file
        if os.path.exists(LOGGING_CONFIG_PATH):
            try:
                with open(LOGGING_CONFIG_PATH, "r") as f:
                    config = yaml.safe_load(f)
                    logging.config.dictConfig(config)
                    console.info(f"Loaded logging configuration from {LOGGING_CONFIG_PATH}")
            except Exception:
                pass

        logging.basicConfig(level=logging.DEBUG)

        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("httpcore").setLevel(logging.WARNING)
        logging.getLogger("anthropic").setLevel(logging.WARNING)
        logging.getLogger("langsmith").setLevel(logging.WARNING)

        formatter = IndentedFormatter("%(levelname)s:%(name)s:%(message)s")
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)

        codeplain_logger = logging.getLogger("codeplain")
        codeplain_logger.addHandler(console_handler)
        codeplain_logger.propagate = False

        llm_logger = logging.getLogger("llm")
        llm_logger.addHandler(console_handler)
        llm_logger.propagate = False

        logging.getLogger("repositories").setLevel(logging.INFO)

    # Check system requirements before proceeding
    system_config.verify_requirements()

    with open(args.filename, "r") as fin:
        plain_source = fin.read()

    template_dirs = file_utils.get_template_directories(args.filename, args.template_dir, DEFAULT_TEMPLATE_DIRS)

    [full_plain_source, loaded_templates] = file_utils.get_loaded_templates(template_dirs, plain_source)

    if args.full_plain:
        if args.verbose:
            console.info("Full plain text:\n")

        console.info(full_plain_source)
        return

    codeplainAPI = codeplain_api.CodeplainAPI(args.api_key)
    codeplainAPI.debug = args.debug
    codeplainAPI.verbose = args.verbose

    if args.api:
        codeplainAPI.api_url = args.api

    console.info(f"Rendering {args.filename} to target code.")

    plain_source_tree = codeplainAPI.get_plain_source_tree(plain_source, loaded_templates)

    if args.render_range is not None:
        args.render_range = get_render_range(args.render_range, plain_source_tree)
    elif args.render_from is not None:
        args.render_range = get_render_range_from(args.render_from, plain_source_tree)

    resources_list = []
    plain_spec.collect_linked_resources(plain_source_tree, resources_list, None, True)

    all_linked_resources = file_utils.load_linked_resources(template_dirs, resources_list)

    frid = plain_spec.get_first_frid(plain_source_tree)

    while frid is not None:
        retry_state = ExecutionState()
        render_functional_requirement(
            args, codeplainAPI, plain_source_tree, frid, all_linked_resources, retry_state, run_state
        )
        frid = plain_spec.get_next_frid(plain_source_tree, frid)

    console.info(f"Render ID: {run_state.render_id}")
    return


def exit_with_error(message, last_successful_frid=None, render_id=None):
    console.error(message)

    if last_successful_frid is not None:
        console.info(
            f"To continue rendering from the last successfully rendered functional requirement, provide the [red][b]--render-from {last_successful_frid}[/b][/red] flag."
        )

    if render_id is not None:
        console.info(f"Render ID: {render_id}")

    sys.exit(1)


if __name__ == "__main__":  # noqa: C901
    args = parse_arguments()

    codeplain_api_module_name = "codeplain_local_api"

    codeplain_api_spec = importlib.util.find_spec(codeplain_api_module_name)
    if args.api or codeplain_api_spec is None:
        if not args.api:
            args.api = "https://api.codeplain.ai"
        if args.debug:
            console.info(f"Running plain2code using REST API at {args.api}.")
        import codeplain_REST_api as codeplain_api
    else:
        if args.debug or not args.full_plain:
            console.info("Running plain2code using local API.\n")

        codeplain_api = importlib.import_module(codeplain_api_module_name)

    if not args.api_key or args.api_key == "":
        exit_with_error(
            "Error: API key is not provided. Please provide an API key using the --api-key flag or by setting the CLAUDE_API_KEY environment variable."
        )
    run_state = RunState(replay_with=args.replay_with)
    if args.debug:
        console.info(f"Render ID: {run_state.render_id}")

    try:
        render(args, run_state)
    except InvalidFridArgument as e:
        console.error(f"Error rendering plain code: {str(e)}.\n")
        # No need to print render ID since this error is going to be thrown at the very start so user will be able to
        # see the render ID that's printed at the very start of the rendering process.
    except FileNotFoundError as e:
        console.error(f"Error rendering plain code: {str(e)}\n")
        if args.debug:
            console.info(f"Render ID: {run_state.render_id}")
            traceback.print_exc()
    except TemplateNotFoundError as e:
        console.error(f"Error: Template not found: {str(e)}\n")
        console.error(system_config.get_error_message("template_not_found"))
    except KeyboardInterrupt:
        console.error("Keyboard interrupt")
        if args.debug:
            # Don't print the traceback here because it's going to be from keyboard interrupt and we don't really care about that
            console.info(f"Render ID: {run_state.render_id}")
    except Exception as e:
        console.error(f"Error rendering plain code: {str(e)}\n")
        if args.debug:
            console.info(f"Render ID: {run_state.render_id}")
            traceback.print_exc()
