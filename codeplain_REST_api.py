import time
from typing import Optional

import requests
from requests.exceptions import ConnectionError, RequestException, Timeout

import plain2code_exceptions
from plain2code_state import RunState

MAX_RETRIES = 4
RETRY_DELAY = 3


class CodeplainAPI:

    def __init__(self, api_key, console):
        self.api_key = api_key
        self.console = console

    @property
    def api_url(self):
        return self._api_url

    @api_url.setter
    def api_url(self, value):
        self._api_url = value

    def _extend_payload_with_run_state(self, payload: dict, run_state: RunState):
        run_state.increment_call_count()
        payload["render_state"] = run_state.to_dict()

    def post_request(self, endpoint_url, headers, payload, run_state: Optional[RunState]):  # noqa: C901
        if run_state is not None:
            self._extend_payload_with_run_state(payload, run_state)

        retry_delay = RETRY_DELAY
        for attempt in range(MAX_RETRIES + 1):
            try:
                response = requests.post(endpoint_url, headers=headers, json=payload)

                try:
                    response_json = response.json()
                except requests.exceptions.JSONDecodeError as e:
                    print(f"Failed to decode JSON response: {e}. Response text: {response.text}")
                    raise

                if response.status_code == requests.codes.bad_request and "error_code" in response_json:
                    if response_json["error_code"] == "FunctionalRequirementTooComplex":
                        raise plain2code_exceptions.FunctionalRequirementTooComplex(
                            response_json["message"], response_json.get("proposed_breakdown")
                        )

                    if response_json["error_code"] == "ConflictingRequirements":
                        raise plain2code_exceptions.ConflictingRequirements(response_json["message"])

                    if response_json["error_code"] == "CreditBalanceTooLow":
                        raise plain2code_exceptions.CreditBalanceTooLow(response_json["message"])

                    if response_json["error_code"] == "LLMInternalError":
                        raise plain2code_exceptions.LLMInternalError(response_json["message"])

                    if response_json["error_code"] == "MissingResource":
                        raise plain2code_exceptions.MissingResource(response_json["message"])

                    if response_json["error_code"] == "PlainSyntaxError":
                        raise plain2code_exceptions.PlainSyntaxError(response_json["message"])

                    if response_json["error_code"] == "OnlyRelativeLinksAllowed":
                        raise plain2code_exceptions.OnlyRelativeLinksAllowed(response_json["message"])

                    if response_json["error_code"] == "LinkMustHaveTextSpecified":
                        raise plain2code_exceptions.LinkMustHaveTextSpecified(response_json["message"])

                    if response_json["error_code"] == "NoRenderFound":
                        raise plain2code_exceptions.NoRenderFound(response_json["message"])

                    if response_json["error_code"] == "MultipleRendersFound":
                        raise plain2code_exceptions.MultipleRendersFound(response_json["message"])

                response.raise_for_status()
                return response_json

            except (ConnectionError, Timeout, RequestException) as e:
                if attempt < MAX_RETRIES:
                    self.console.info(f"Connection error on attempt {attempt + 1}/{MAX_RETRIES + 1}: {e}")
                    self.console.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    # Exponential backoff
                    retry_delay *= 2
                else:
                    self.console.error(f"Max retries ({MAX_RETRIES}) exceeded. Last error: {e}")
                    raise RequestException(
                        f"Connection error: Unable to reach the Codeplain API at {self.api_url}. Please try again or contact support."
                    )

    def get_plain_source_tree(self, plain_source, loaded_templates, run_state: RunState):
        """
        Builds plain source tree from the given plain text source in Markdown format.

        Args:
            plain_source (str): A string containing the plain text source to be parsed.
            loaded_templates (dict): A dictionary containing the loaded templates.

        Returns:
            dict: A plain source tree.

        Raises:
            Exception: If parsing of plain_source fails.
        """
        endpoint_url = f"{self.api_url}/plain_source_tree"
        headers = {"X-API-Key": self.api_key, "Content-Type": "application/json"}

        payload = {"plain_source": plain_source, "loaded_templates": loaded_templates}

        return self.post_request(endpoint_url, headers, payload, run_state)

    def render_functional_requirement(
        self,
        frid,
        plain_source_tree,
        linked_resources,
        existing_files_content,
        run_state: RunState,
    ):
        """
        Renders the content of a functional requirement based on the provided ID,
        plain source tree, and existing files' content.

        Args:
            frid (str): The unique identifier for the functional requirement to be rendered.
            plain_source_tree (dict): A dictionary containing the plain source tree.
            linked_resources (dict): A dictionary where the keys represent resource names
                                    and the values are the content of those resources.
            existing_files_content (dict): A dictionary where the keys represent code base
                                        filenames and the values are the content of those files.

        Returns:
            str: A string containing the rendered functional requirement, formatted
                appropriately based on the inputs.

        Raises:
            ValueError: If the frid is invalid or the necessary plain source tree is not valid.
        """
        endpoint_url = f"{self.api_url}/render_functional_requirement"
        headers = {"X-API-Key": self.api_key, "Content-Type": "application/json"}

        payload = {
            "frid": frid,
            "plain_source_tree": plain_source_tree,
            "linked_resources": linked_resources,
            "existing_files_content": existing_files_content,
        }

        return self.post_request(endpoint_url, headers, payload, run_state)

    def fix_unittests_issue(
        self,
        frid,
        plain_source_tree,
        linked_resources,
        existing_files_content,
        unittests_issue,
        run_state: RunState,
    ):
        endpoint_url = f"{self.api_url}/fix_unittests_issue"
        headers = {"X-API-Key": self.api_key, "Content-Type": "application/json"}

        payload = {
            "frid": frid,
            "plain_source_tree": plain_source_tree,
            "linked_resources": linked_resources,
            "existing_files_content": existing_files_content,
            "unittests_issue": unittests_issue,
            "unittest_batch_id": run_state.unittest_batch_id,
        }

        return self.post_request(endpoint_url, headers, payload, run_state)

    def refactor_source_files_if_needed(self, frid, files_to_check, existing_files_content, run_state: RunState):
        endpoint_url = f"{self.api_url}/refactor_source_files_if_needed"
        headers = {"X-API-Key": self.api_key, "Content-Type": "application/json"}

        payload = {
            "frid": frid,
            "files_to_check": list(files_to_check),
            "existing_files_content": existing_files_content,
        }

        return self.post_request(endpoint_url, headers, payload, run_state)

    def render_conformance_tests(
        self,
        frid,
        functional_requirement_id,
        plain_source_tree,
        linked_resources,
        existing_files_content,
        conformance_tests_folder_name,
        conformance_tests_json,
        all_acceptance_tests,
        run_state: RunState,
    ):
        endpoint_url = f"{self.api_url}/render_conformance_tests"
        headers = {"X-API-Key": self.api_key, "Content-Type": "application/json"}

        payload = {
            "frid": frid,
            "functional_requirement_id": functional_requirement_id,
            "plain_source_tree": plain_source_tree,
            "linked_resources": linked_resources,
            "existing_files_content": existing_files_content,
            "conformance_tests_folder_name": conformance_tests_folder_name,
            "conformance_tests_json": conformance_tests_json,
            "all_acceptance_tests": all_acceptance_tests,
        }

        response = self.post_request(endpoint_url, headers, payload, run_state)
        return response["patched_response_files"], response["conformance_tests_plan_summary_string"]

    def generate_folder_name_from_functional_requirement(
        self,
        frid,
        functional_requirement,
        existing_folder_names,
        run_state: RunState,
    ):
        endpoint_url = f"{self.api_url}/generate_folder_name_from_functional_requirement"
        headers = {"X-API-Key": self.api_key, "Content-Type": "application/json"}

        payload = {
            "frid": frid,
            "functional_requirement": functional_requirement,
            "existing_folder_names": existing_folder_names,
        }

        return self.post_request(endpoint_url, headers, payload, run_state)

    def fix_conformance_tests_issue(
        self,
        frid,
        functional_requirement_id,
        plain_source_tree,
        linked_resources,
        existing_files_content,
        code_diff,
        conformance_tests_files,
        acceptance_tests,
        conformance_tests_issue,
        implementation_fix_count,
        conformance_tests_folder_name,
        current_testing_frid_high_level_implementation_plan: Optional[str],
        run_state: RunState,
    ):
        endpoint_url = f"{self.api_url}/fix_conformance_tests_issue"
        headers = {"X-API-Key": self.api_key, "Content-Type": "application/json"}

        payload = {
            "frid": frid,
            "functional_requirement_id": functional_requirement_id,
            "plain_source_tree": plain_source_tree,
            "linked_resources": linked_resources,
            "existing_files_content": existing_files_content,
            "code_diff": code_diff,
            "conformance_tests_files": conformance_tests_files,
            "conformance_tests_issue": conformance_tests_issue,
            "implementation_fix_count": implementation_fix_count,
            "conformance_tests_folder_name": conformance_tests_folder_name,
            "current_testing_frid_high_level_implementation_plan": current_testing_frid_high_level_implementation_plan,
        }

        if acceptance_tests is not None:
            payload["acceptance_tests"] = acceptance_tests

        return self.post_request(endpoint_url, headers, payload, run_state)

    def render_acceptance_tests(
        self,
        frid,
        plain_source_tree,
        linked_resources,
        existing_files_content,
        conformance_tests_files,
        acceptance_test,
        run_state: RunState,
    ):
        """
        Renders acceptance tests based on the provided parameters.

        Args:
            frid (str): The unique identifier for the functional requirement.
            plain_source_tree (dict): A dictionary containing the plain source tree.
            linked_resources (dict): A dictionary where the keys represent resource names
                                    and the values are the content of those resources.
            existing_files_content (dict): A dictionary where the keys represent code base
                                        filenames and the values are the content of those files.
            conformance_tests_files (dict): A dictionary containing conformance test files.
            acceptance_test (dict): A dictionary containing acceptance test information.

        Returns:
            dict: The rendered acceptance tests.

        Raises:
            Exception: If the request fails or returns an error.
        """
        endpoint_url = f"{self.api_url}/render_acceptance_tests"
        headers = {"X-API-Key": self.api_key, "Content-Type": "application/json"}

        payload = {
            "frid": frid,
            "plain_source_tree": plain_source_tree,
            "linked_resources": linked_resources,
            "existing_files_content": existing_files_content,
            "conformance_tests_files": conformance_tests_files,
            "acceptance_test": acceptance_test,
        }

        return self.post_request(endpoint_url, headers, payload, run_state)

    def analyze_rendering(
        self,
        frid,
        plain_source_tree,
        linked_resources,
        existing_files_content,
        implementation_code_diff,
        fixed_implementation_code_diff,
        run_state: RunState,
    ):
        endpoint_url = f"{self.api_url}/analyze_rendering"
        headers = {"X-API-Key": self.api_key, "Content-Type": "application/json"}

        payload = {
            "frid": frid,
            "plain_source_tree": plain_source_tree,
            "linked_resources": linked_resources,
            "existing_files_content": existing_files_content,
            "implementation_code_diff": implementation_code_diff,
            "fixed_implementation_code_diff": fixed_implementation_code_diff,
        }

        return self.post_request(endpoint_url, headers, payload, run_state)

    def finish_functional_requirement(self, frid, run_state: RunState):
        endpoint_url = f"{self.api_url}/finish_functional_requirement"
        headers = {"X-API-Key": self.api_key, "Content-Type": "application/json"}

        payload = {
            "frid": frid,
        }

        return self.post_request(endpoint_url, headers, payload, run_state)

    def summarize_finished_conformance_tests(
        self,
        frid,
        plain_source_tree,
        linked_resources,
        conformance_test_files_content,
        run_state: RunState,
    ):
        endpoint_url = f"{self.api_url}/summarize_finished_conformance_tests"
        headers = {"X-API-Key": self.api_key, "Content-Type": "application/json"}
        payload = {
            "frid": frid,
            "plain_source_tree": plain_source_tree,
            "linked_resources": linked_resources,
            "conformance_test_files_content": conformance_test_files_content,
        }

        return self.post_request(endpoint_url, headers, payload, run_state)
