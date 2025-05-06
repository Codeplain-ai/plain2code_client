import argparse
import importlib.util
import json
import logging
import os
import shutil
import subprocess
import sys
import tempfile
import traceback

import file_utils
import plain_spec
from codeplain_REST_api import CodeplainAPI
from plain2code_console import console
from plain2code_state import Codebase

TEST_SCRIPT_EXECUTION_TIMEOUT = 120  # 120 seconds

CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
DEFAULT_BUILD_FOLDER = "build"
DEFAULT_CONFORMANCE_TESTS_FOLDER = "conformance_tests"
CONFORMANCE_TESTS_BACKUP_FOLDER_SUFFIX = ".backup"
CONFORMANCE_TESTS_DEFINITION_FILE_NAME = "conformance_tests.json"
DEFAULT_TEMPLATE_DIRS = "standard_template_library"

MAX_UNITTEST_FIX_ATTEMPTS = 10
MAX_CONFORMANCE_TEST_FIX_ATTEMPTS = 10
MAX_CONFORMANCE_TEST_RUNS = 10
MAX_REFACTORING_ITERATIONS = 5
MAX_UNIT_TEST_RENDER_RETRIES = 2


class InvalidRenderRange(Exception):
    pass


def non_empty_string(s):
    if not s:
        raise argparse.ArgumentTypeError("The string cannot be empty.")
    return s


def get_render_range(render_range, plain_source_tree):
    if render_range is None:
        raise InvalidRenderRange("Invalid render range.")

    render_range = render_range.split(",")
    if len(render_range) < 1 or len(render_range) > 2:
        raise InvalidRenderRange("Invalid render range.")

    if len(render_range) == 1:
        render_range.append(render_range[0])

    frids = list(plain_spec.get_frids(plain_source_tree))

    if render_range[0] not in frids or render_range[1] not in frids:
        raise InvalidRenderRange("Invalid render range.")

    start_idx = frids.index(render_range[0])
    end_idx = frids.index(render_range[1]) + 1

    if start_idx >= end_idx:
        raise InvalidRenderRange("Invalid render range.")

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
    args, codeplainAPI, frid, plain_source_tree, linked_resources, existing_files
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
            console.print_files(
                "Files sent for fixing unit tests:",
                args.build_folder,
                existing_files_content,
                style=console.INPUT_STYLE,
            )

        with console.status(f"[{console.INFO_STYLE}]Fixing unit tests issue..."):
            response_files = codeplainAPI.fix_unittests_issue(
                frid, plain_source_tree, linked_resources, existing_files_content, unittests_issue
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
):
    specifications, _ = plain_spec.get_specifications_for_frid(plain_source_tree, functional_requirement_id)
    if args.verbose:
        console.info("\n[b]Implementing test requirements:[/b]")
        console.print_list(specifications[plain_spec.TEST_REQUIREMENTS], style=console.INFO_STYLE)

    if not conformance_tests_folder_name:
        try:
            existing_folder_names = file_utils.list_folders_in_directory(args.conformance_tests_folder)
        except FileNotFoundError:
            existing_folder_names = []

        fr_subfolder_name = codeplainAPI.generate_folder_name_from_functional_requirement(
            frid=frid,
            functional_requirement=specifications[plain_spec.FUNCTIONAL_REQUIREMENTS][-1],
            existing_folder_names=existing_folder_names,
        )

        if args.verbose:
            console.info(f"Storing conformance test files in subfolder {fr_subfolder_name}")

        conformance_tests_folder_name = os.path.join(args.conformance_tests_folder, fr_subfolder_name)

    file_utils.delete_files_and_subfolders(conformance_tests_folder_name, args.debug)

    if args.verbose:
        console.print_files(
            "Files sent for generating conformance tests:",
            args.build_folder,
            existing_files_content,
            style=console.INPUT_STYLE,
        )

    with console.status(f"[{console.INFO_STYLE}]Generating conformance tests..."):
        response_files = codeplainAPI.render_conformance_tests(
            frid, functional_requirement_id, plain_source_tree, linked_resources, existing_files_content
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
):
    recreated_conformance_tests = False
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
                f"Conformance tests script {args.conformance_tests_script} for {conformance_tests_folder_name} still failed after {conformance_test_fix_count - 1} attemps at fixing issues."
            )
            if recreated_conformance_tests:
                console.error(
                    "We've already tried to fix the issue by recreating the conformance tests but tests still fail. Please fix the issues manually."
                )
                sys.exit(1)

            console.info("[b]Recreating conformance tests.[/b]")

            if args.verbose:
                console.print_files(
                    "Files sent for recreating conformance tests:",
                    args.build_folder,
                    existing_files_content,
                    style=console.INPUT_STYLE,
                )
            generate_conformance_tests(
                args,
                codeplainAPI,
                frid,
                functional_requirement_id,
                plain_source_tree,
                linked_resources,
                existing_files_content,
                conformance_tests_folder_name,
            )

            recreated_conformance_tests = True
            conformance_test_fix_count = 0
            implementation_fix_count = 1
            conformance_tests_files = file_utils.list_all_text_files(conformance_tests_folder_name)
            continue

        conformance_tests_files_content = file_utils.get_existing_files_content(
            conformance_tests_folder_name, conformance_tests_files
        )

        if args.verbose:
            console.print_files(
                "Current implementation files sent for fixing conformance tests:",
                args.build_folder,
                existing_files_content,
                style=console.INPUT_STYLE,
            )

            console.print_files(
                "Existing conformance tests files sent for fixing:",
                conformance_tests_folder_name,
                conformance_tests_files_content,
                style=console.INPUT_STYLE,
            )

        try:
            with console.status(f"[{console.INFO_STYLE}]Fixing conformance tests..."):
                [conformance_tests_fixed, response_files] = codeplainAPI.fix_conformance_tests_issue(
                    frid,
                    functional_requirement_id,
                    plain_source_tree,
                    linked_resources,
                    existing_files_content,
                    code_diff,
                    conformance_tests_files_content,
                    conformance_tests_issue,
                    implementation_fix_count,
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
                        args,
                        codeplainAPI,
                        frid,
                        plain_source_tree,
                        linked_resources,
                        existing_files,
                    )

                    if not unittests_success:
                        # TODO: Address this edge case in different way in the next pull request.
                        print(
                            f"Unittests failed to update after successfully fixing conformance tests for functional requirement {functional_requirement_id}."
                        )
                        sys.exit(1)

                    return [True, existing_files]

                console.info(
                    f"Couldn't fix conformance tests issue in folder {conformance_tests_folder_name} for functional requirement {functional_requirement_id}. Trying one more time."
                )
                implementation_fix_count += 1
        except codeplain_api.ConflictingRequirements as e:
            console.error(f"Conflicting requirements. {str(e)}.")
            sys.exit(1)
        except Exception as e:
            console.error(f"Error fixing conformance tests issue: {str(e)}")
            sys.exit(1)

    return [False, existing_files]


def conformance_testing(
    args,
    codeplainAPI,
    frid,
    plain_source_tree,
    linked_resources,
    existing_files,
    conformance_tests,
):
    conformance_tests_run_count = 0
    specifications, _ = plain_spec.get_specifications_for_frid(plain_source_tree, frid)
    while conformance_tests_run_count < MAX_CONFORMANCE_TEST_RUNS:
        conformance_tests_run_count += 1
        implementation_code_has_changed = False
        existing_files_content = file_utils.get_existing_files_content(args.build_folder, existing_files)

        if args.verbose:
            console.info(f"Running conformance tests attempt {conformance_tests_run_count}.")

        if frid == plain_spec.get_first_frid(plain_source_tree):
            code_diff = {}
        else:
            previous_build_folder = args.build_folder + "." + plain_spec.get_previous_frid(plain_source_tree, frid)
            if not os.path.exists(previous_build_folder):
                raise Exception(f"Build folder {previous_build_folder} not found: ")

            code_diff = file_utils.get_folders_diff(previous_build_folder, args.build_folder)

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
                )

            conformance_tests_folder_name = conformance_tests[functional_requirement_id]["folder_name"]

            [implementation_code_has_changed, existing_files] = run_conformance_tests(
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
            )

            if functional_requirement_id == frid:
                break
            else:
                functional_requirement_id = plain_spec.get_next_frid(plain_source_tree, functional_requirement_id)

        if implementation_code_has_changed:
            continue

        return conformance_tests

    console.error(
        f"Conformance tests still failed after {conformance_tests_run_count} attemtps at fixing issues. Please fix the issues manually."
    )
    sys.exit(1)


class IndentedFormatter(logging.Formatter):

    def format(self, record):
        original_message = record.getMessage()

        modified_message = original_message.replace("\n", "\n                ")

        record.msg = modified_message
        return super().format(record)


# TODO: Once we'll be refactoring and working with this method, we should also adjust cognitive complexity.
def render_functional_requirement(  # noqa: C901
    args, codeplainAPI: CodeplainAPI, plain_source_tree, frid, all_linked_resources
):

    if args.render_range is not None and frid not in args.render_range:
        if args.verbose:
            console.info("\n-------------------------------------")
            console.status(f"Skipping rendering iteration: {frid}\n")
            console.info("-------------------------------------\n")

        return

    specifications, _ = plain_spec.get_specifications_for_frid(plain_source_tree, frid)

    is_first_frid = frid == plain_spec.get_first_frid(plain_source_tree)

    if args.verbose:
        console.info("\n-------------------------------------")
        console.info(f"Rendering functional requirement {frid}")
        console.info(f"[b]{specifications[plain_spec.FUNCTIONAL_REQUIREMENTS][-1]}[/b]")
        console.info("-------------------------------------\n")

    if os.path.isdir(args.build_folder):
        if args.debug:
            console.debug(f"Deleting content of the build folder {args.build_folder}.")

        if not args.dry_run:
            file_utils.delete_files_and_subfolders(args.build_folder, args.debug)
    else:
        if args.debug and is_first_frid:
            console.debug(f"Build folder {args.build_folder} does not exist. Creating it.")

        if not args.dry_run:
            os.makedirs(args.build_folder)

    if is_first_frid:
        if args.base_folder:
            previous_build_folder = args.base_folder
            if not os.path.exists(previous_build_folder):
                raise Exception(f"Base folder {previous_build_folder} not found: ")
        else:
            previous_build_folder = None
    else:
        previous_build_folder = args.build_folder + "." + plain_spec.get_previous_frid(plain_source_tree, frid)

        if not args.dry_run:
            if not os.path.exists(previous_build_folder):
                raise Exception(f"Build folder {previous_build_folder} not found: ")

            if os.path.exists(args.conformance_tests_folder):
                conformance_tests_backup_folder = args.conformance_tests_folder + CONFORMANCE_TESTS_BACKUP_FOLDER_SUFFIX
                if os.path.exists(conformance_tests_backup_folder):
                    shutil.rmtree(conformance_tests_backup_folder)

                # Copy the entire directory tree
                shutil.copytree(args.conformance_tests_folder, conformance_tests_backup_folder)

                if args.debug:
                    console.debug("Conformance tests folder successfully backed up.")

    resources_list = []
    plain_spec.collect_linked_resources(plain_source_tree, resources_list, frid)

    linked_resources = {}
    for resource in resources_list:
        linked_resources[resource["target"]] = all_linked_resources[resource["target"]]

    if previous_build_folder:
        existing_files = file_utils.list_all_text_files(previous_build_folder)
        existing_files_content = file_utils.get_existing_files_content(previous_build_folder, existing_files)
    else:
        existing_files = []
        existing_files_content = {}

    conformance_tests_definition_file_name = os.path.join(
        args.conformance_tests_folder, CONFORMANCE_TESTS_DEFINITION_FILE_NAME
    )
    try:
        with open(conformance_tests_definition_file_name, "r") as f:
            conformance_tests = json.load(f)
    except FileNotFoundError:
        conformance_tests = {}

    if args.dry_run:
        if args.verbose:
            console.warning("\n== Dry run: not actually rendering the functional requirement. ==\n")
        return

    # Create a snapshot of the initial state before rendering begins
    initial_state = Codebase()
    initial_state.save_state(existing_files, set(), previous_build_folder)

    functional_requirement_render_attempt = 0
    while True:
        functional_requirement_render_attempt += 1
        if args.verbose:
            console.info(
                f"Rerendering functional requirement {frid}, attempt number {functional_requirement_render_attempt}."
            )

        # Phase 1: Render the functional requirement.
        try:
            if args.verbose and existing_files_content:
                console.print_files(
                    "Files sent to code generation:",
                    args.build_folder,
                    existing_files_content,
                    style=console.INPUT_STYLE,
                )
            with console.status(f"[{console.INFO_STYLE}]Generating functional requirement..."):
                response_files = codeplainAPI.render_functional_requirement(
                    frid, plain_source_tree, linked_resources, existing_files_content
                )
        except codeplain_api.FunctionalRequirementTooComplex as e:
            # TODO: Suggest how to break down the functional requirement. Identified options are:
            # - Split the functional requirement into smaller parts.
            # - If the functional requirement changes multiple entities, first limit the changes to a single representative entity and then to all entities.
            # - Move the functional requirement higher up, that is, to come earlier in the rendering order.
            console.error(
                f"Too many files or code lines generated. You should break down the functional requirement into smaller parts ({str(e)})."
            )
            sys.exit(1)

        existing_files, changed_files = file_utils.update_build_folder_with_rendered_files(
            previous_build_folder, args.build_folder, existing_files, response_files, args.debug
        )
        if args.verbose:
            console.print_files("Files generated:", args.build_folder, response_files, style=console.OUTPUT_STYLE)

        # Phase 2: Run and patch unittests.
        console.info("\n[b]Running and patching unittests...[/b]")

        [existing_files, tmp_changed_files, unittest_success] = run_unittests(
            args,
            codeplainAPI,
            frid,
            plain_source_tree,
            linked_resources,
            existing_files,
        )

        if unittest_success:
            for file_name in tmp_changed_files:
                if file_name not in existing_files:
                    if file_name in changed_files:
                        changed_files.remove(file_name)
                else:
                    changed_files.add(file_name)
            break

        # If unittests generation&patching failed for the first time => retry rendering functional requirement
        # If it failed for the second time => we're unable to fix the issue => exit with an error
        if functional_requirement_render_attempt < MAX_UNIT_TEST_RENDER_RETRIES:
            console.info(
                "Unittests failed to update after rendering the functional requirement."
                f"Restarting rendering the functional requirement {frid} from scratch."
            )
            existing_files, changed_files = initial_state.restore_state(args.build_folder)
            continue

        console.error(
            f"Unittests failed to update after rendering the functional requirement {frid} for the {functional_requirement_render_attempt} time."
        )
        sys.exit(1)

    # Create a snapshot of the state before refactoring
    pre_refactoring_state = Codebase()
    pre_refactoring_state.save_state(existing_files, changed_files, args.build_folder)

    # Phase 3: Refactor the source code if needed.
    console.info("[b]Refactoring the generated code...[/b]")
    num_refactoring_iterations = 0
    while num_refactoring_iterations < MAX_REFACTORING_ITERATIONS:
        num_refactoring_iterations += 1
        if args.verbose:
            console.info(f"\nRefactoring iteration {num_refactoring_iterations}.")

        existing_files_content = file_utils.get_existing_files_content(args.build_folder, existing_files)
        if args.verbose:
            console.print_files(
                "Files sent for refactoring:", args.build_folder, existing_files_content, style=console.INPUT_STYLE
            )
        with console.status(f"[{console.INFO_STYLE}]Refactoring the generated code..."):
            response_files = codeplainAPI.refactor_source_files_if_needed(
                frid=frid,
                files_to_check=changed_files,
                existing_files_content=existing_files_content,
            )

        if len(response_files) == 0:
            if args.verbose:
                console.info("No files refactored.")
            break

        build_folder_copy = args.build_folder + "." + frid + "." + str(num_refactoring_iterations - 1)
        if args.verbose:
            console.info(f"Some files refactored. Storing a copy of current build folder to {build_folder_copy}")

        if os.path.exists(build_folder_copy) and os.path.isdir(build_folder_copy):
            file_utils.delete_files_and_subfolders(build_folder_copy)

        for file_name in existing_files:
            file_utils.copy_file(os.path.join(args.build_folder, file_name), os.path.join(build_folder_copy, file_name))

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
        )

        if not unittest_success:
            # Revert to the last known good state
            if args.verbose:
                console.info(
                    f"Refactoring iteration {num_refactoring_iterations} was not successful for the functional requirement {frid}. "
                    f"Reverting to the previous valid state and retrying again."
                )
            existing_files, changed_files = pre_refactoring_state.restore_state(args.build_folder)
            continue

        for file_name in tmp_changed_files:
            if file_name not in existing_files:
                if file_name in changed_files:
                    changed_files.remove(file_name)
            else:
                changed_files.add(file_name)

        # Update the last known good state since refactoring was successful
        pre_refactoring_state.save_state(existing_files, changed_files, args.build_folder)

    # Phase 4: Conformance test the code.
    console.info("\n[b]Implementing conformance tests...[/b]\n")
    if (
        args.conformance_tests_script
        and plain_spec.TEST_REQUIREMENTS in specifications
        and specifications[plain_spec.TEST_REQUIREMENTS]
    ):
        conformance_tests = conformance_testing(
            args,
            codeplainAPI,
            frid,
            plain_source_tree,
            linked_resources,
            existing_files,
            conformance_tests,
        )

        if os.path.exists(args.conformance_tests_folder):
            if args.verbose:
                console.info(f"Storing conformance tests definition to {conformance_tests_definition_file_name}")

            with open(conformance_tests_definition_file_name, "w") as f:
                json.dump(conformance_tests, f, indent=4)

    if plain_spec.get_next_frid(plain_source_tree, frid) is not None and (
        args.render_range is None or frid in args.render_range
    ):

        previous_build_folder = args.build_folder + "." + frid
        if args.debug:
            console.debug(f"Renaming build folder to {previous_build_folder}")

        if os.path.exists(previous_build_folder) and os.path.isdir(previous_build_folder):
            file_utils.delete_files_and_subfolders(previous_build_folder)
            os.rmdir(previous_build_folder)

        os.rename(args.build_folder, previous_build_folder)

    return


def render(args):

    if args.verbose:
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

    with open(args.filename, "r") as fin:
        plain_source = fin.read()

    template_dirs = [
        os.path.dirname(args.filename),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), DEFAULT_TEMPLATE_DIRS),
    ]

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

    resources_list = []
    plain_spec.collect_linked_resources(plain_source_tree, resources_list)

    all_linked_resources = file_utils.load_linked_resources(os.path.dirname(args.filename), resources_list)

    frid = plain_spec.get_first_frid(plain_source_tree)
    while frid is not None:
        render_functional_requirement(args, codeplainAPI, plain_source_tree, frid, all_linked_resources)
        frid = plain_spec.get_next_frid(plain_source_tree, frid)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Render plain code to target code.")
    parser.add_argument("filename", type=str, help="plain file to render")
    parser.add_argument("--verbose", "-v", action="store_true", help="enable verbose output")
    parser.add_argument("--debug", action="store_true", help="enable debug information")
    parser.add_argument("--base-folder", type=str, help="base folder for the build files")
    parser.add_argument(
        "--build-folder", type=non_empty_string, default=DEFAULT_BUILD_FOLDER, help="folder for build files"
    )
    parser.add_argument("--render-range", type=str, help="which functional requirements should be generated")
    parser.add_argument("--unittests-script", type=str, help="a script to run unit tests")
    parser.add_argument(
        "--conformance-tests-folder",
        type=non_empty_string,
        default=DEFAULT_CONFORMANCE_TESTS_FOLDER,
        help="folder for conformance test files",
    )
    parser.add_argument("--conformance-tests-script", type=str, help="a script to run conformance tests")
    parser.add_argument(
        "--api", type=str, nargs="?", const="https://api.codeplain.ai", help="force using the API (for internal use)"
    )
    parser.add_argument(
        "--api-key",
        type=str,
        default=CLAUDE_API_KEY,
        help="API key used to access the API. If not provided, the CLAUDE_API_KEY environment variable is used.",
    )
    parser.add_argument("--full-plain", action="store_true", help="emit full plain text to render")
    parser.add_argument(
        "--dry-run", action="store_true", help="preview what plain2code would do without actually making any changes"
    )

    args = parser.parse_args()

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
        console.error(
            "Error: API key is not provided. Please provide an API key using the --api-key flag or by setting the CLAUDE_API_KEY environment variable."
        )
        sys.exit(1)

    try:
        render(args)
    except InvalidRenderRange as e:
        console.error(f"Error rendering plain code: {str(e)}. Invalid render range: {args.render_range}\n")
    except FileNotFoundError as e:
        console.error(f"Error rendering plain code: {str(e)}\n")
    except Exception as e:
        console.error(f"Error rendering plain code: {str(e)}\n")
        traceback.print_exc()
