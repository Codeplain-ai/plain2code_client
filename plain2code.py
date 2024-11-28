import sys
import os
import copy
import subprocess
import argparse
import json
import importlib.util
import logging

import plain_spec
import file_utils

CLAUDE_API_KEY = os.getenv('CLAUDE_API_KEY')
DEFAULT_BUILD_FOLDER = 'build'
DEFAULT_E2E_TESTS_FOLDER = "e2e_tests"
E2E_TESTS_DEFINITION_FILE_NAME = "e2e_tests.json"

MAX_UNITTEST_FIX_ATTEMPTS = 10
MAX_E2E_TEST_FIX_ATTEMPTS = 10
MAX_E2E_TEST_RUNS = 10
MAX_REFACTORING_ITERATIONS = 5


def non_empty_string(s):
    if not s:
        raise argparse.ArgumentTypeError("The string cannot be empty.")
    return s


def get_render_range(render_range):
    render_range = render_range.split(',')
    if len(render_range) < 1 or len(render_range) > 2:
        raise Exception("Invalid render range.")

    range_start = int(render_range[0])
    if len(render_range) == 1:
        range_end = range_start + 1
    else:
        range_end = int(render_range[1]) + 1

    if range_start >= range_end:
        raise Exception("Invalid render range.")

    return range(range_start, range_end)


def print_response_files_summary(response_files):
    for file_name in response_files:
        if response_files[file_name] is None:
            print("- " + file_name + " (deleted)")
        else:
            print("- " + file_name)


def execute_test_script(test_script, scripts_args, verbose):
    
    result = subprocess.run(
        [file_utils.add_current_path_if_no_path(test_script)] + scripts_args,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )

    if verbose:
        print(f"Test script output (exit code:{result.returncode}):\n{result.stdout}")

    if result.returncode != 0:
        return result.stdout
    else:
        return None
    

def run_unittests(args, codeplainAPI, frid, plain_sections, linked_resources, existing_files):

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

        response_files = codeplainAPI.fix_unittests_issue(frid, plain_sections, linked_resources, existing_files_content, unittests_issue)

        changed_files.update(response_files.keys())

        existing_files = file_utils.store_response_files(args.build_folder, response_files, existing_files)
        print("Files fixed:")
        print_response_files_summary(response_files)

    return existing_files, changed_files


def generate_end_to_end_tests(args, codeplainAPI, frid, plain_sections, linked_resources, existing_files, e2e_tests_folder_name):
    if args.verbose:
        print(f"\nImplementing test requirements:\n{plain_sections[plain_spec.TEST_REQUIREMENTS]['markdown']}")

    if not e2e_tests_folder_name:
        try:
            existing_folder_names = file_utils.list_folders_in_directory(args.e2e_tests_folder)
        except FileNotFoundError:
            existing_folder_names = []
    
        fr_subfolder_name = codeplainAPI.generate_folder_name_from_functional_requirement(
            plain_sections[plain_spec.FUNCTIONAL_REQUIREMENTS][frid - 1]['markdown'],
            existing_folder_names
        )

        if args.verbose:
            print(f"Storing e2e test files in subfolder {fr_subfolder_name}")

        e2e_tests_folder_name = os.path.join(args.e2e_tests_folder, fr_subfolder_name)

    file_utils.delete_files_and_subfolders(e2e_tests_folder_name, args.verbose)

    existing_files_content = file_utils.get_existing_files_content(args.build_folder, existing_files)

    response_files = codeplainAPI.render_e2e_tests(frid, plain_sections, linked_resources, existing_files_content)

    e2e_tests_files = file_utils.store_response_files(e2e_tests_folder_name, response_files, [])

    print("\nEnd-to-end test files generated:")
    print('\n'.join(["- " + file_name for file_name in response_files.keys()]) + '\n')

    return {
        'functional_requirement': plain_sections[plain_spec.FUNCTIONAL_REQUIREMENTS][frid - 1]['markdown'],
        'folder_name' : e2e_tests_folder_name
    }


def run_e2e_tests(args, codeplainAPI, frid, functional_requirement_id, plain_sections, linked_resources, existing_files, existing_files_content, code_diff, e2e_tests_folder_name):
    e2e_test_fix_count = 0
    implementation_fix_count = 1
    e2e_tests_files = file_utils.list_all_files(e2e_tests_folder_name)
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
                frid, functional_requirement_id, plain_sections, linked_resources, existing_files_content, code_diff, e2e_tests_files_content, e2e_tests_issue, implementation_fix_count
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

                    [existing_files, _] = run_unittests(args, codeplainAPI, frid, plain_sections, linked_resources, existing_files)

                    return [True, existing_files]

                print(f"Couldn't fix end-to-end tests issue in folder {e2e_tests_folder_name} for functional requirement {functional_requirement_id}. Trying one more time.")
                implementation_fix_count += 1
        except codeplain_api.ConflictingRequirements as e:
            print(f"Conflicting requirements. {str(e)}.")
            exit()
        except Exception as e:
            print(f"Error fixing end-to-end tests issue: {str(e)}")
            sys.exit(1)

    if e2e_tests_issue:
        print(f"End-to-end tests script {args.e2e_tests_script} for {e2e_tests_folder_name} still failed after {e2e_test_fix_count - 1} attemps at fixing issues. Please fix the issues manually.")
        sys.exit(1)
    
    return [False, existing_files]


def end_to_end_testing(args, codeplainAPI, frid, plain_sections, linked_resources, existing_files, e2e_tests):
    e2e_tests_run_count = 0
    while e2e_tests_run_count < MAX_E2E_TEST_RUNS:
        e2e_tests_run_count += 1
        implementation_code_has_changed = False
        existing_files_content = file_utils.get_existing_files_content(args.build_folder, existing_files)

        if args.verbose:
            print(f"Running end-to-end tests attempt {e2e_tests_run_count}.")

        if frid == 1:
            code_diff = {}
        else:
            previous_build_folder = args.build_folder + "." + str(frid - 1)
            if not os.path.exists(previous_build_folder):
                raise Exception(f"Build folder {previous_build_folder} not found: ")
        
            code_diff = file_utils.get_folders_diff(previous_build_folder, args.build_folder)

        for functional_requirement_id in range(1, frid + 1):
            if (functional_requirement_id == frid) and \
                (str(frid) not in e2e_tests or \
                 e2e_tests[str(frid)]['functional_requirement'] != plain_sections[plain_spec.FUNCTIONAL_REQUIREMENTS][frid - 1]['markdown']):

                if str(frid) in e2e_tests:
                    e2e_tests_folder_name = e2e_tests[str(frid)]['folder_name']
                else:
                    e2e_tests_folder_name = None

                e2e_tests[str(frid)] = generate_end_to_end_tests(args, codeplainAPI, frid, plain_sections, linked_resources, existing_files, e2e_tests_folder_name)

            e2e_tests_folder_name = e2e_tests[str(functional_requirement_id)]['folder_name']

            [implementation_code_has_changed, existing_files] = run_e2e_tests(args, codeplainAPI, frid, functional_requirement_id, plain_sections, linked_resources, existing_files, existing_files_content, code_diff, e2e_tests_folder_name)

            if implementation_code_has_changed:
                break

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
        linked_resources_str = "\n".join(["- " + resource_name for resource_name in plain_section['linked_resources']])
        print(f"Linked resources:\n{linked_resources_str}\n\n")


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

    codeplainAPI = codeplain_api.CodeplainAPI(args.api_key)
    codeplainAPI.debug = args.debug
    codeplainAPI.verbose = args.verbose

    if args.api:
        codeplainAPI.api_url = args.api
    
    plain_sections = codeplainAPI.get_plain_sections(plain_source)

    print(f"Rendering {args.filename} to target code.\n")

    if args.verbose:
        print(f"Definitions:\n{plain_sections[plain_spec.DEFINITIONS]['markdown']}")
        print_linked_resources(plain_sections[plain_spec.DEFINITIONS])

        print(f"Non-Functional Requirements:\n{plain_sections[plain_spec.NON_FUNCTIONAL_REQUIREMENTS]['markdown']}")
        print_linked_resources(plain_sections[plain_spec.NON_FUNCTIONAL_REQUIREMENTS])

        if plain_spec.TEST_REQUIREMENTS in plain_sections:
            print(f"Test Requirements:\n{plain_sections[plain_spec.TEST_REQUIREMENTS]['markdown']}")
            print_linked_resources(plain_sections[plain_spec.TEST_REQUIREMENTS])

    resources_map = file_utils.get_linked_resources(plain_sections)
    all_linked_resources = file_utils.load_linked_resources(os.path.dirname(args.filename), resources_map)
    
    e2e_tests_definition_file_name = os.path.join(args.e2e_tests_folder, E2E_TESTS_DEFINITION_FILE_NAME)
    try:
        with open(e2e_tests_definition_file_name, 'r') as f:
            e2e_tests = json.load(f)
    except FileNotFoundError:
        e2e_tests = {}

    for frid in range(1, len(plain_sections[plain_spec.FUNCTIONAL_REQUIREMENTS]) + 1):

        if args.render_range is not None and frid not in args.render_range:
            if args.verbose:
                print("Skipping rendering iteration: " + str(frid) + "\n")

            continue

        file_utils.delete_files_and_subfolders(args.build_folder, args.verbose)

        if frid == 1:
            if args.base_folder:
                previous_build_folder = args.base_folder
                if not os.path.exists(previous_build_folder):
                    raise Exception(f"Base folder {previous_build_folder} not found: ")
            else:
                previous_build_folder = None
        else:
            previous_build_folder = args.build_folder + "." + str(frid - 1)
            if not os.path.exists(previous_build_folder):
                raise Exception(f"Build folder {previous_build_folder} not found: ")

        rendering_plain_sections = copy.deepcopy(plain_sections)
        rendering_plain_sections[plain_spec.FUNCTIONAL_REQUIREMENTS] = rendering_plain_sections[plain_spec.FUNCTIONAL_REQUIREMENTS][:frid]
        resources_map = file_utils.get_linked_resources(rendering_plain_sections)

        linked_resources = {}
        for key, value in resources_map.items():
            linked_resources[key] = {
                'content': all_linked_resources[key]['content'],
                'sections': value
            }

        if previous_build_folder:
            existing_files = file_utils.list_all_files(previous_build_folder)
            existing_files_content = file_utils.get_existing_files_content(previous_build_folder, existing_files)
        else:
            existing_files = []
            existing_files_content = {}

        if args.verbose:
            print("\nImplementing functional requirement:")
            print(plain_sections[plain_spec.FUNCTIONAL_REQUIREMENTS][frid - 1]['markdown'])

        try:
            response_files = codeplainAPI.render_functional_requirement(frid, plain_sections, linked_resources, existing_files_content, )
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

        [existing_files, tmp_changed_files] = run_unittests(args, codeplainAPI, frid, plain_sections, linked_resources, existing_files)

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

            build_folder_copy = args.build_folder + "." + str(frid) + "." + str(num_refactoring_iterations - 1)
            if args.verbose:
                print(f"    Some files refactored. Storing a copy of current build folder to {build_folder_copy}")

            if os.path.exists(build_folder_copy) and os.path.isdir(build_folder_copy):
                file_utils.delete_files_and_subfolders(build_folder_copy)
            
            for file_name in existing_files:
                file_utils.copy_file(os.path.join(args.build_folder, file_name), os.path.join(build_folder_copy, file_name))

            existing_files = file_utils.store_response_files(args.build_folder, response_files, existing_files)
            print("Files refactored:")
            print('\n'.join(response_files.keys()))

            [existing_files, tmp_changed_files] = run_unittests(args, codeplainAPI, frid, plain_sections, linked_resources, existing_files)
            changed_files.update(tmp_changed_files)

        if args.e2e_tests_script and plain_spec.TEST_REQUIREMENTS in plain_sections and plain_sections[plain_spec.TEST_REQUIREMENTS]:
            e2e_tests = end_to_end_testing(args, codeplainAPI, frid, plain_sections, linked_resources, existing_files, e2e_tests)

            if os.path.exists(args.e2e_tests_folder):
                if args.verbose:
                    print(f"Storing e2e tests definition to {e2e_tests_definition_file_name}")

                with open(e2e_tests_definition_file_name, "w") as f:
                    json.dump(e2e_tests, f, indent=4)

        if frid < len(plain_sections[plain_spec.FUNCTIONAL_REQUIREMENTS])  and \
            (args.render_range is None or (frid + 1) in args.render_range):

            previous_build_folder = args.build_folder + "." + str(frid)
            if args.verbose:
                print(f"Renaming build folder to {previous_build_folder}")

            if os.path.exists(previous_build_folder) and os.path.isdir(previous_build_folder):
                file_utils.delete_files_and_subfolders(previous_build_folder)
                os.rmdir(previous_build_folder)

            os.rename(args.build_folder, previous_build_folder)


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

    if args.render_range is not None:
        args.render_range = get_render_range(args.render_range)

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
    except Exception as e:
        print(f"Error rendering plain code: {str(e)}")
