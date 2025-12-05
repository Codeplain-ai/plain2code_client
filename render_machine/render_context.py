from typing import Optional

import file_utils
import git_utils
import plain_spec
from codeplain_REST_api import CodeplainAPI
from plain2code_console import console
from plain2code_state import CONFORMANCE_TESTS_DEFINITION_FILE_NAME, ConformanceTestsUtils, RunState
from render_machine import triggers
from render_machine.conformance_test_helpers import ConformanceTestHelpers
from render_machine.render_types import ConformanceTestsRunningContext, FridContext, UnitTestsRunningContext

DEFAULT_TEMPLATE_DIRS = "standard_template_library"

MAX_UNITTEST_FIX_ATTEMPTS = 20
MAX_CODE_GENERATION_RETRIES = 2
MAX_CONFORMANCE_TEST_RERENDER_ATTEMPTS = 1
MAX_REFACTORING_ITERATIONS = 5
MAX_CONFORMANCE_TEST_FIX_ATTEMPTS = 20
MAX_FUNCTIONAL_REQUIREMENT_RENDER_ATTEMPTS_FAILED_UNIT_DURING_CONFORMANCE_TESTS = 2


class RenderContext:
    def __init__(self, codeplain_api, plain_source_tree: dict, args: dict, run_state: RunState):
        self.codeplain_api: CodeplainAPI = codeplain_api
        self.plain_source_tree = plain_source_tree
        self.args = args
        self.run_state = run_state
        self.starting_frid = None

        template_dirs = file_utils.get_template_directories(args.filename, args.template_dir, DEFAULT_TEMPLATE_DIRS)
        resources_list = []
        plain_spec.collect_linked_resources(plain_source_tree, resources_list, None, True)
        self.all_linked_resources = file_utils.load_linked_resources(template_dirs, resources_list)

        # Initialize context objects
        self.frid_context: Optional[FridContext] = None
        self.unit_tests_running_context: Optional[UnitTestsRunningContext] = None
        self.conformance_tests_running_context: Optional[ConformanceTestsRunningContext] = None
        # Constants that should remain for a single frid, but possible over multiple rerenderings of the same frid
        self.functional_requirements_render_attempts_failed_unit_during_conformance_tests = 0
        # Initialize conformance tests utilities
        self.conformance_tests_utils = ConformanceTestsUtils(
            conformance_tests_folder=args.conformance_tests_folder,
            conformance_tests_definition_file_name=CONFORMANCE_TESTS_DEFINITION_FILE_NAME,
            verbose=args.verbose,
        )

        self.machine = None

    def set_machine(self, machine):
        self.machine = machine

    def start_implementing_frid(self):
        if self.starting_frid is not None:
            frid = self.starting_frid
            self.starting_frid = None
        elif self.frid_context is None:
            frid = plain_spec.get_first_frid(self.plain_source_tree)
        else:
            frid = plain_spec.get_next_frid(self.plain_source_tree, self.frid_context.frid)

        if frid is None:
            # If frid context is empty, it means that all frids have been implemented
            self.frid_context = None
            self.machine.dispatch(triggers.PREPARE_FINAL_OUTPUT)
            return

        specifications, _ = plain_spec.get_specifications_for_frid(self.plain_source_tree, frid)
        functional_requirement_text = specifications[plain_spec.FUNCTIONAL_REQUIREMENTS][-1]

        resources_list = []
        plain_spec.collect_linked_resources(self.plain_source_tree, resources_list, None, True, frid)

        linked_resources = {}
        for resource in resources_list:
            linked_resources[resource["target"]] = self.all_linked_resources[resource["target"]]

        self.frid_context = FridContext(
            frid=frid,
            specifications=specifications,
            functional_requirement_text=functional_requirement_text,
            linked_resources=linked_resources,
            functional_requirement_render_attempts=0,
        )

    def check_frid_iteration_limit(self):
        # If frid context is not set, it means that all frids have been implemented
        if self.frid_context is None:
            return

        if self.frid_context.functional_requirement_render_attempts >= MAX_CODE_GENERATION_RETRIES:
            console.error(
                f"Unittests could not be fixed after rendering the functional requirement {self.frid_context.frid} for the {MAX_CODE_GENERATION_RETRIES} times."
            )
            self.machine.dispatch(triggers.HANDLE_ERROR)

        self.frid_context.functional_requirement_render_attempts += 1

        if self.frid_context.functional_requirement_render_attempts > 1:
            # this if is intended just for logging
            console.info(
                f"Unittests could not be fixed after rendering the functional requirement. "
                f"Restarting rendering the functional requirement {self.frid_context.frid} from scratch."
            )

    def finish_implementing_frid(self):
        self.functional_requirements_render_attempts_failed_unit_during_conformance_tests = 0
        pass

    def start_unittests_processing(self):
        self.unit_tests_running_context = UnitTestsRunningContext(fix_attempts=0)
        self.run_state.increment_unittest_batch_id()

    def start_unittests_processing_in_conformance_tests(self):
        self.start_unittests_processing()
        # set to first FRID
        self.conformance_tests_running_context.current_testing_frid = plain_spec.get_first_frid(self.plain_source_tree)

    def finish_unittests_processing(self):
        existing_files = file_utils.list_all_text_files(self.args.build_folder)

        # TODO: Double check if this logic is what we want
        for file_name in self.unit_tests_running_context.changed_files:
            if file_name not in existing_files:
                self.frid_context.changed_files.discard(file_name)
            else:
                self.frid_context.changed_files.add(file_name)
        self.unit_tests_running_context.fix_attempts = 1

    def start_fixing_unit_tests(self):
        self.unit_tests_running_context.fix_attempts += 1

        if self.unit_tests_running_context.fix_attempts > MAX_UNITTEST_FIX_ATTEMPTS:
            self.machine.dispatch(triggers.RESTART_FRID_PROCESSING)

    def start_fixing_unit_tests_in_conformance_tests(self):
        self.unit_tests_running_context.fix_attempts += 1

        if self.unit_tests_running_context.fix_attempts > MAX_UNITTEST_FIX_ATTEMPTS:
            self.functional_requirements_render_attempts_failed_unit_during_conformance_tests += 1
            if (
                self.functional_requirements_render_attempts_failed_unit_during_conformance_tests
                >= MAX_FUNCTIONAL_REQUIREMENT_RENDER_ATTEMPTS_FAILED_UNIT_DURING_CONFORMANCE_TESTS
            ):
                console.error(
                    f"Failed to adjust unit tests after implementation code was update while fixing conformance tests for functional requirement {self.frid_context.frid} for the {MAX_FUNCTIONAL_REQUIREMENT_RENDER_ATTEMPTS_FAILED_UNIT_DURING_CONFORMANCE_TESTS} times."
                )
                self.machine.dispatch(triggers.HANDLE_ERROR)
            else:
                console.info(
                    f"Failed to adjust unit tests after implementation code was update while fixing conformance tests for functional requirement {self.frid_context.frid}."
                )
                console.info(f"Restarting rendering the functional requirement {self.frid_context.frid} from scratch.")
                self.machine.dispatch(triggers.RESTART_FRID_PROCESSING)

    def start_fixing_unit_tests_in_refactoring(self):
        self.unit_tests_running_context.fix_attempts += 1

        if self.unit_tests_running_context.fix_attempts > MAX_UNITTEST_FIX_ATTEMPTS:
            git_utils.revert_changes(self.args.build_folder)
            self.machine.dispatch(triggers.START_NEW_REFACTORING_ITERATION)

    def start_refactoring_code(self):

        if self.frid_context.refactoring_iteration == 0:
            console.info("\n[b]Refactoring the generated code...[/b]\n")

        self.frid_context.refactoring_iteration += 1

        if self.frid_context.refactoring_iteration >= MAX_REFACTORING_ITERATIONS:
            if self.args.verbose:
                console.info(
                    f"Refactoring iterations limit of {MAX_REFACTORING_ITERATIONS} reached for functional requirement {self.frid_context.frid}."
                )
            self.machine.dispatch(triggers.PROCEED_FRID_PROCESSING)

    def start_testing_environment_preparation(self):
        if (
            self.args.prepare_environment_script is None
            or not self.conformance_tests_running_context.should_prepare_testing_environment
        ):
            self.machine.dispatch(triggers.MARK_TESTING_ENVIRONMENT_PREPARED)

    def start_conformance_tests_processing(self):
        console.info("\n[b]Implementing conformance tests...[/b]\n")
        conformance_tests_json = self.conformance_tests_utils.get_conformance_tests_json()
        self.conformance_tests_running_context = ConformanceTestsRunningContext(
            current_testing_frid=None,
            current_testing_frid_specifications=None,
            conformance_test_phase_index=0,
            fix_attempts=0,
            conformance_tests_json=conformance_tests_json,
            conformance_tests_render_attempts=0,
            should_prepare_testing_environment=True,
        )

    def finish_conformance_tests_processing(self):
        self.conformance_tests_running_context = None

    def start_conformance_tests_for_frid(self):
        if self.conformance_tests_running_context.regenerating_conformance_tests:
            if self.args.verbose:
                console.info(
                    f"Recreating conformance tests for functional requirement {self.conformance_tests_running_context.current_testing_frid}."
                )

            existing_conformance_tests_folder = self.conformance_tests_running_context.conformance_tests_json.pop(
                self.conformance_tests_running_context.current_testing_frid
            )

            file_utils.delete_folder(existing_conformance_tests_folder["folder_name"])

            self.conformance_tests_running_context.conformance_tests_render_attempts += 1
            self.conformance_tests_running_context.fix_attempts = 0
            self.conformance_tests_running_context.regenerating_conformance_tests = False
        else:
            if self.conformance_tests_running_context.current_testing_frid == self.frid_context.frid:

                if not self.frid_context.specifications.get(
                    plain_spec.ACCEPTANCE_TESTS
                ) or self.conformance_tests_running_context.conformance_test_phase_index == len(
                    self.frid_context.specifications[plain_spec.ACCEPTANCE_TESTS]
                ):
                    self.machine.dispatch(triggers.MARK_ALL_CONFORMANCE_TESTS_PASSED)
                    return

                should_reset_high_level_implementation_plan = (
                    self.conformance_tests_running_context.current_testing_frid == self.frid_context.frid
                    and self.conformance_tests_running_context.conformance_test_phase_index == 0
                )
                if should_reset_high_level_implementation_plan:
                    self.conformance_tests_running_context.current_testing_frid_high_level_implementation_plan = None

                self.conformance_tests_running_context.conformance_test_phase_index += 1
                current_acceptance_tests = self.frid_context.specifications[plain_spec.ACCEPTANCE_TESTS][
                    : self.conformance_tests_running_context.conformance_test_phase_index
                ]
                self.conformance_tests_running_context.conformance_tests_json[self.frid_context.frid][
                    plain_spec.ACCEPTANCE_TESTS
                ] = current_acceptance_tests
                return

            if self.conformance_tests_running_context.current_testing_frid is None:
                self.conformance_tests_running_context.current_testing_frid = plain_spec.get_first_frid(
                    self.plain_source_tree
                )
            else:
                self.conformance_tests_running_context.current_testing_frid = plain_spec.get_next_frid(
                    self.plain_source_tree, self.conformance_tests_running_context.current_testing_frid
                )
            self.conformance_tests_running_context.current_testing_frid_specifications, _ = (
                plain_spec.get_specifications_for_frid(
                    self.plain_source_tree, self.conformance_tests_running_context.current_testing_frid
                )
            )
            if ConformanceTestHelpers.current_conformance_tests_exist(self.conformance_tests_running_context):  # type: ignore
                self.machine.dispatch(triggers.MARK_CONFORMANCE_TESTS_READY)

    def start_fixing_conformance_tests(self):
        self.conformance_tests_running_context.fix_attempts += 1

        if self.conformance_tests_running_context.fix_attempts >= MAX_CONFORMANCE_TEST_FIX_ATTEMPTS:
            if (
                self.conformance_tests_running_context.conformance_tests_render_attempts
                >= MAX_CONFORMANCE_TEST_RERENDER_ATTEMPTS
            ):
                console.error(
                    f"We've already tried to fix the issue by recreating the conformance tests but tests still fail. Please fix the issues manually. FRID: {self.frid_context.frid}, Render ID: {self.run_state.render_id}"
                )
                self.machine.dispatch(triggers.HANDLE_ERROR)
            else:
                self.conformance_tests_running_context.regenerating_conformance_tests = True
                self.machine.dispatch(triggers.MARK_REGENERATION_OF_CONFORMANCE_TESTS)

    def finish_fixing_conformance_tests(self):
        if self.args.verbose:
            console.info(
                f"[b]Running conformance tests attempt {self.conformance_tests_running_context.fix_attempts + 1}.[/b]"
            )
