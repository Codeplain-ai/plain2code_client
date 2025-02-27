import sys
import os
import subprocess
import argparse
import json
import importlib.util
import logging
import traceback

import plain_spec
import file_utils

TEST_SCRIPT_EXECUTION_TIMEOUT = 120 # 120 seconds

CLAUDE_API_KEY = os.getenv('CLAUDE_API_KEY')
DEFAULT_BUILD_FOLDER = 'build'
DEFAULT_E2E_TESTS_FOLDER = "e2e_tests"
E2E_TESTS_DEFINITION_FILE_NAME = "e2e_tests.json"

MAX_UNITTEST_FIX_ATTEMPTS = 10
MAX_E2E_TEST_FIX_ATTEMPTS = 10
MAX_E2E_TEST_RUNS = 10
MAX_REFACTORING_ITERATIONS = 5


class InvalidRenderRange(Exception):
    pass


def non_empty_string(s):
    if not s:
        raise argparse.ArgumentTypeError("The string cannot be empty.")
    return s


def get_render_range(render_range, plain_source_tree):
    if render_range is None:
        raise InvalidRenderRange("Invalid render range.")

    render_range = render_range.split(',')
    if len(render_range) < 1 or len(render_range) > 2:
        raise InvalidRenderRange("Invalid render range.")

    if len(render_range) == 1:
        render_range.append(render_range[0])

    frids = []
    for frid in plain_spec.get_frids(plain_source_tree):
        frids.append(frid)

    if render_range[0] not in frids or render_range[1] not in frids:
        raise InvalidRenderRange("Invalid render range.")

    start_idx = frids.index(render_range[0])
    end_idx = frids.index(render_range[1]) + 1

    if start_idx >= end_idx:
        raise InvalidRenderRange("Invalid render range.")

    return frids[start_idx:end_idx]


def print_response_files_summary(response_files):
    for file_name in response_files:
        if response_files[file_name] is None:
            print("- " + file_name + " (deleted)")
        else:
            print("- " + file_name)


def execute_test_script(test_script, scripts_args, verbose):
    try:
        result = subprocess.run(
            [file_utils.add_current_path_if_no_path(test_script)] + scripts_args,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=TEST_SCRIPT_EXECUTION_TIMEOUT
        )

        if verbose:
            print(f"Test script output (exit code:{result.returncode}):\n{result.stdout}")

        if result.returncode != 0:
            return result.stdout
        else:
            return None
    except subprocess.TimeoutExpired:
        if verbose:
            print(f"Test script {test_script} timed out after {TEST_SCRIPT_EXECUTION_TIMEOUT} seconds.")

        return f"Tests did not finish in {TEST_SCRIPT_EXECUTION_TIMEOUT} seconds."

def run_unittests(args, codeplainAPI, frid, plain_source_tree, linked_resources, existing_files):

    changed_files = set()
    
    if not args.unittests_script:
        return existing_files, changed_files
    
    if args.verbose:
        print("Running unit tests script:", args.unittests_script)

    unit_test_run_count = 0
    while True:
        unit_test_run_count += 1

        if args.verbose:
            print(f"Running unit tests attempt {unit_test_run_count}.")

        unittests_issue = execute_test_script(args.unittests_script, [args.build_folder], args.verbose)

        if not unittests_issue:
            break

        if unit_test_run_count > MAX_UNITTEST_FIX_ATTEMPTS:
            print(f"Unit tests still failed after {unit_test_run_count - 1} attemps at fixing issues. Please fix the issues manually.")
            sys.exit(1)

        existing_files_content = file_utils.get_existing_files_content(args.build_folder, existing_files)

        response_files = codeplainAPI.fix_unittests_issue(frid, plain_source_tree, linked_resources, existing_files_content, unittests_issue)

        changed_files.update(response_files.keys())

        existing_files = file_utils.store_response_files(args.build_folder, response_files, existing_files)
        print("Files fixed:")
        print_response_files_summary(response_files)

    return existing_files, changed_files


def generate_end_to_end_tests(args, codeplainAPI, frid, plain_source_tree, linked_resources, existing_files, e2e_tests_folder_name):
    specifications = plain_spec.get_specifications_for_frid(plain_source_tree, frid)
    if args.verbose:
        # TODO: Print the definitions.
        print(f"\nImplementing test requirements:")
        print("\n".join(specifications[plain_spec.TEST_REQUIREMENTS]))
        print()

    if not e2e_tests_folder_name:
        try:
            existing_folder_names = file_utils.list_folders_in_directory(args.e2e_tests_folder)
        except FileNotFoundError:
            existing_folder_names = []
    
        fr_subfolder_name = codeplainAPI.generate_folder_name_from_functional_requirement(
            specifications[plain_spec.FUNCTIONAL_REQUIREMENTS][-1],
            existing_folder_names
        )

        if args.verbose:
            print(f"Storing e2e test files in subfolder {fr_subfolder_name}")

        e2e_tests_folder_name = os.path.join(args.e2e_tests_folder, fr_subfolder_name)

    file_utils.delete_files_and_subfolders(e2e_tests_folder_name, args.verbose)

    existing_files_content = file_utils.get_existing_files_content(args.build_folder, existing_files)

    response_files = codeplainAPI.render_e2e_tests(frid, plain_source_tree, linked_resources, existing_files_content)

    e2e_tests_files = file_utils.store_response_files(e2e_tests_folder_name, response_files, [])

    print("\nEnd-to-end test files generated:")
    print('\n'.join(["- " + file_name for file_name in response_files.keys()]) + '\n')

    return {
        'functional_requirement': specifications[plain_spec.FUNCTIONAL_REQUIREMENTS][-1],
        'folder_name' : e2e_tests_folder_name
    }


def run_e2e_tests(args, codeplainAPI, frid, functional_requirement_id, plain_source_tree, linked_resources, existing_files, existing_files_content, code_diff, e2e_tests_folder_name):
    e2e_test_fix_count = 0
    implementation_fix_count = 1
    e2e_tests_files = file_utils.list_all_text_files(e2e_tests_folder_name)
    while True:
        e2e_test_fix_count += 1

        if args.verbose:
            print(f"\nRunning end-to-end tests script {args.e2e_tests_script} for {e2e_tests_folder_name} (functional requirement {functional_requirement_id}, attempt: {e2e_test_fix_count}).")

        e2e_tests_issue = execute_test_script(args.e2e_tests_script, [args.build_folder, e2e_tests_folder_name], args.verbose)

        if not e2e_tests_issue or e2e_test_fix_count > MAX_E2E_TEST_FIX_ATTEMPTS:
            break

        e2e_tests_files_content = file_utils.get_existing_files_content(e2e_tests_folder_name, e2e_tests_files)

        try:
            [e2e_tests_fixed, response_files] = codeplainAPI.fix_e2e_tests_issue(
                frid, functional_requirement_id, plain_source_tree, linked_resources, existing_files_content, code_diff, e2e_tests_files_content, e2e_tests_issue, implementation_fix_count
            )

            if e2e_tests_fixed:
                e2e_tests_files = file_utils.store_response_files(e2e_tests_folder_name, response_files, e2e_tests_files)
                print(f"\nEnd-to-end test files in folder {e2e_tests_folder_name} fixed:")
                print_response_files_summary(response_files)

                implementation_fix_count = 1
            else:
                if len(response_files) > 0:
                    existing_files = file_utils.store_response_files(args.build_folder, response_files, existing_files)
                    print("Files fixed:")
                    print_response_files_summary(response_files)

                    [existing_files, _] = run_unittests(args, codeplainAPI, frid, plain_source_tree, linked_resources, existing_files)

                    return [True, existing_files]

                print(f"Couldn't fix end-to-end tests issue in folder {e2e_tests_folder_name} for functional requirement {functional_requirement_id}. Trying one more time.")
                implementation_fix_count += 1
        except codeplain_api.ConflictingRequirements as e:
            print(f"Conflicting requirements. {str(e)}.")
            sys.exit(1)
        except Exception as e:
            print(f"Error fixing end-to-end tests issue: {str(e)}")
            sys.exit(1)

    if e2e_tests_issue:
        print(f"End-to-end tests script {args.e2e_tests_script} for {e2e_tests_folder_name} still failed after {e2e_test_fix_count - 1} attemps at fixing issues. Please fix the issues manually.")
        sys.exit(1)
    
    return [False, existing_files]


def end_to_end_testing(args, codeplainAPI, frid, plain_source_tree, linked_resources, existing_files, e2e_tests):
    e2e_tests_run_count = 0
    specifications = plain_spec.get_specifications_for_frid(plain_source_tree, frid)
    while e2e_tests_run_count < MAX_E2E_TEST_RUNS:
        e2e_tests_run_count += 1
        implementation_code_has_changed = False
        existing_files_content = file_utils.get_existing_files_content(args.build_folder, existing_files)

        if args.verbose:
            print(f"Running end-to-end tests attempt {e2e_tests_run_count}.")

        if frid == plain_spec.get_first_frid(plain_source_tree):
            code_diff = {}
        else:
            previous_build_folder = args.build_folder + "." + plain_spec.get_previous_frid(plain_source_tree, frid)
            if not os.path.exists(previous_build_folder):
                raise Exception(f"Build folder {previous_build_folder} not found: ")
        
            code_diff = file_utils.get_folders_diff(previous_build_folder, args.build_folder)

        functional_requirement_id = plain_spec.get_first_frid(plain_source_tree)
        while functional_requirement_id is not None and not implementation_code_has_changed:
            if (functional_requirement_id == frid) and \
                (frid not in e2e_tests or \
                 e2e_tests[frid]['functional_requirement'] != specifications[plain_spec.FUNCTIONAL_REQUIREMENTS][-1]):

                if frid in e2e_tests:
                    e2e_tests_folder_name = e2e_tests[frid]['folder_name']
                else:
                    e2e_tests_folder_name = None

                e2e_tests[frid] = generate_end_to_end_tests(args, codeplainAPI, frid, plain_source_tree, linked_resources, existing_files, e2e_tests_folder_name)

            e2e_tests_folder_name = e2e_tests[functional_requirement_id]['folder_name']

            [implementation_code_has_changed, existing_files] = run_e2e_tests(args, codeplainAPI, frid, functional_requirement_id, plain_source_tree, linked_resources, existing_files, existing_files_content, code_diff, e2e_tests_folder_name)

            if functional_requirement_id == frid:
                break
            else:
                functional_requirement_id = plain_spec.get_next_frid(plain_source_tree, functional_requirement_id)

        if implementation_code_has_changed:
            continue

        return e2e_tests

    print(f"End-to-end tests still failed after {e2e_tests_run_count - 1} attemps at fixing issues. Please fix the issues manually.")
    sys.exit(1)


class IndentedFormatter(logging.Formatter):

    def format(self, record):
        original_message = record.getMessage()
        
        modified_message = original_message.replace('\n', '\n                ')

        record.msg = modified_message
        return super().format(record)
    

def print_linked_resources(plain_section):
    if 'linked_resources' in plain_section:
        linked_resources_str = "\n".join([f"- {resource_name['text']} ({resource_name['target']})"  for resource_name in plain_section['linked_resources']])
        print(f"Linked resources:\n{linked_resources_str}\n\n")


def render_functional_requirement(args, codeplainAPI, plain_source_tree, frid, all_linked_resources):

    if args.render_range is not None and frid not in args.render_range:
        if args.verbose:
            print(f"\n-------------------------------------")
            print(f"Skipping rendering iteration: {frid}\n")

        return

    specifications = plain_spec.get_specifications_for_frid(plain_source_tree, frid)
        
    if args.verbose:
        print(f"\n-------------------------------------")
        print(f"Rendering functional requirement {frid}")

        if len(specifications[plain_spec.DEFINITIONS]) > 0:
            print("\nDefinitions:")
            print('\n'.join(specifications[plain_spec.DEFINITIONS]))

        print("\nNon-Functional Requirements:")
        print('\n'.join(specifications[plain_spec.NON_FUNCTIONAL_REQUIREMENTS]))

        if len(specifications[plain_spec.TEST_REQUIREMENTS]) > 0:
            print("\nTest Requirements:")
            print('\n'.join(specifications[plain_spec.TEST_REQUIREMENTS]))

        print("\nFunctional Requirement:")
        print(specifications[plain_spec.FUNCTIONAL_REQUIREMENTS][-1])

        print()

    if os.path.isdir(args.build_folder):
        if args.verbose:
            print(f"Deleting content of the build folder {args.build_folder}.")

        file_utils.delete_files_and_subfolders(args.build_folder, args.verbose)
    else:
        if args.verbose and frid == plain_spec.get_first_frid(plain_source_tree):
            print(f"Build folder {args.build_folder} does not exist. Creating it.")

        os.makedirs(args.build_folder)

    if frid == plain_spec.get_first_frid(plain_source_tree):
        if args.base_folder:
            previous_build_folder = args.base_folder
            if not os.path.exists(previous_build_folder):
                raise Exception(f"Base folder {previous_build_folder} not found: ")
        else:
            previous_build_folder = None
    else:
        previous_build_folder = args.build_folder + "." + plain_spec.get_previous_frid(plain_source_tree, frid)
        if not os.path.exists(previous_build_folder):
            raise Exception(f"Build folder {previous_build_folder} not found: ")

    resources_list = []
    plain_spec.collect_linked_resources(plain_source_tree, resources_list, frid)

    linked_resources = {}
    for resource in resources_list:
        linked_resources[resource['target']] = all_linked_resources[resource['target']]

    if previous_build_folder:
        existing_files = file_utils.list_all_text_files(previous_build_folder)
        existing_files_content = file_utils.get_existing_files_content(previous_build_folder, existing_files)
    else:
        existing_files = []
        existing_files_content = {}

    e2e_tests_definition_file_name = os.path.join(args.e2e_tests_folder, E2E_TESTS_DEFINITION_FILE_NAME)
    try:
        with open(e2e_tests_definition_file_name, 'r') as f:
            e2e_tests = json.load(f)
    except FileNotFoundError:
        e2e_tests = {}

    try:
        response_files = codeplainAPI.render_functional_requirement(frid, plain_source_tree, linked_resources, existing_files_content)
    except codeplain_api.FunctionalRequirementTooComplex as e:
        # TODO: Suggest how to break down the functional requirement. Identified options are:
        # - Split the functional requirement into smaller parts.
        # - If the functional requirement changes multiple entities, first limit the changes to a single representative entity and then to all entities.
        # - Move the functional requirement higher up, that is, to come earlier in the rendering order.
        print(f"Too many files or code lines generated. You should break down the functional requirement into smaller parts ({str(e)}).")
        sys.exit(1)

    if previous_build_folder:
        for file_name in existing_files:
            if file_name not in response_files:
                if args.verbose:
                    print("Copying file: ", file_name)

                file_utils.copy_file(os.path.join(previous_build_folder, file_name), os.path.join(args.build_folder, file_name))

    changed_files = set()
    changed_files.update(response_files.keys())

    existing_files = file_utils.store_response_files(args.build_folder, response_files, existing_files)
    print("Files generated:")
    print('\n'.join(["- " + file_name for file_name in response_files.keys()]))

    [existing_files, tmp_changed_files] = run_unittests(args, codeplainAPI, frid, plain_source_tree, linked_resources, existing_files)
    
    changed_files.update(tmp_changed_files)

    num_refactoring_iterations = 0
    while num_refactoring_iterations < MAX_REFACTORING_ITERATIONS:
        num_refactoring_iterations += 1
        if args.verbose:
            print(f"\nRefactoring iteration {num_refactoring_iterations}.")

        existing_files_content = file_utils.get_existing_files_content(args.build_folder, existing_files)
        response_files = codeplainAPI.refactor_source_files_if_needed(changed_files, existing_files_content)

        if len(response_files) == 0:
            if args.verbose:
                print("    No files refactored.")
            break

        build_folder_copy = args.build_folder + "." + frid + "." + str(num_refactoring_iterations - 1)
        if args.verbose:
            print(f"    Some files refactored. Storing a copy of current build folder to {build_folder_copy}")

        if os.path.exists(build_folder_copy) and os.path.isdir(build_folder_copy):
            file_utils.delete_files_and_subfolders(build_folder_copy)
        
        for file_name in existing_files:
            file_utils.copy_file(os.path.join(args.build_folder, file_name), os.path.join(build_folder_copy, file_name))

        existing_files = file_utils.store_response_files(args.build_folder, response_files, existing_files)
        print("Files refactored:")
        print('\n'.join(response_files.keys()))

        [existing_files, tmp_changed_files] = run_unittests(args, codeplainAPI, frid, plain_source_tree, linked_resources, existing_files)
        changed_files.update(tmp_changed_files)

    if args.e2e_tests_script and plain_spec.TEST_REQUIREMENTS in specifications and specifications[plain_spec.TEST_REQUIREMENTS]:
        e2e_tests = end_to_end_testing(args, codeplainAPI, frid, plain_source_tree, linked_resources, existing_files, e2e_tests)

        if os.path.exists(args.e2e_tests_folder):
            if args.verbose:
                print(f"Storing e2e tests definition to {e2e_tests_definition_file_name}")

            with open(e2e_tests_definition_file_name, "w") as f:
                json.dump(e2e_tests, f, indent=4)

    if plain_spec.get_next_frid(plain_source_tree, frid) is not None  and \
        (args.render_range is None or frid in args.render_range):

        previous_build_folder = args.build_folder + "." + frid
        if args.verbose:
            print(f"\nRenaming build folder to {previous_build_folder}")

        if os.path.exists(previous_build_folder) and os.path.isdir(previous_build_folder):
            file_utils.delete_files_and_subfolders(previous_build_folder)
            os.rmdir(previous_build_folder)

        os.rename(args.build_folder, previous_build_folder)


def render(args):

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)

        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("httpcore").setLevel(logging.WARNING)
        logging.getLogger("anthropic").setLevel(logging.WARNING)

        formatter = IndentedFormatter('%(levelname)s:%(name)s:%(message)s')
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)

        codeplain_logger = logging.getLogger('codeplain')
        codeplain_logger.addHandler(console_handler)
        codeplain_logger.propagate = False

        llm_logger = logging.getLogger('llm')
        llm_logger.addHandler(console_handler)
        llm_logger.propagate = False

    with open(args.filename, "r") as fin:
        plain_source = fin.read()

    loaded_templates = file_utils.get_loaded_templates(os.path.dirname(args.filename), plain_source)

    codeplainAPI = codeplain_api.CodeplainAPI(args.api_key)
    codeplainAPI.debug = args.debug
    codeplainAPI.verbose = args.verbose

    if args.api:
        codeplainAPI.api_url = args.api

    print(f"Rendering {args.filename} to target code.")
    
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

    parser = argparse.ArgumentParser(description='Render plain code to target code.')
    parser.add_argument('filename', type=str, help='plain file to render')
    parser.add_argument('--verbose', '-v', action='store_true', help='enable verbose output')
    parser.add_argument('--debug', action='store_true', help='enable debug information')
    parser.add_argument('--base-folder', type=str, help='base folder for the build files')
    parser.add_argument("--build-folder", type=non_empty_string, default=DEFAULT_BUILD_FOLDER, help="folder for build files")
    parser.add_argument('--render-range', type=str, help='which functional requirements should be generated')
    parser.add_argument('--unittests-script', type=str, help='a script to run unit tests')
    parser.add_argument('--e2e-tests-folder', type=non_empty_string, default=DEFAULT_E2E_TESTS_FOLDER, help='folder for e2e test files')
    parser.add_argument('--e2e-tests-script', type=str, help='a script to run e2e tests')
    parser.add_argument('--api', type=str, nargs='?', const="https://api.codeplain.ai", help='force using the API (for internal use)')
    parser.add_argument('--api-key', type=str, default=CLAUDE_API_KEY, help='API key used to access the API. If not provided, the CLAUDE_API_KEY environment variable is used.')

    args = parser.parse_args()

    codeplain_api_module_name = 'codeplain_local_api'

    codeplain_api_spec = importlib.util.find_spec(codeplain_api_module_name)
    if args.api or codeplain_api_spec is None:
        if not args.api:
            args.api = "https://api.codeplain.ai"
        print(f"Running plain2code using REST API at {args.api }\n")
        import codeplain_REST_api as codeplain_api
    else:
        print(f"Running plain2code using local API.\n")
        codeplain_api = importlib.import_module(codeplain_api_module_name)

    try:
        render(args)
    except InvalidRenderRange as e:
        print(f"Error rendering plain code. Invalid render range: {args.render_range}\n")
    except Exception as e:
        print(f"Error rendering plain code: {str(e)}\n")
        traceback.print_exc()
