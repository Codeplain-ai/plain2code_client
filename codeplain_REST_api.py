import json
import requests


class FunctionalRequirementTooComplex(Exception):
    pass


class ConflictingRequirements(Exception):
    pass


class CreditBalanceTooLow(Exception):
    pass


class LLMOverloadedError(Exception):
    pass


class MissingResource(Exception):
    pass


class CodeplainAPI:
    
    def __init__(self, api_key):
        self.api_key = api_key

    
    @property
    def api_url(self):
        return self._api_url


    @api_url.setter
    def api_url(self, value):
        self._api_url = value


    def post_request(self, endpoint_url, headers, payload):
        response = requests.post(endpoint_url, headers=headers, json=payload)

        # First check if the response was successful
        response.raise_for_status()

        try:
            response_json = response.json()
        except requests.exceptions.JSONDecodeError as e:
            print(f"Failed to decode JSON response. Response text: {response.text}")
            raise

        if response.status_code == requests.codes.bad_request and "error_code" in response_json:
            if response_json["error_code"] == 'FunctionalRequirementTooComplex':
                raise FunctionalRequirementTooComplex(response_json['message'])
            
            if response_json["error_code"] == 'ConflictingRequirements':
                raise ConflictingRequirements(response_json['message'])
            
            if response_json["error_code"] == 'CreditBalanceTooLow':
                raise CreditBalanceTooLow(response_json['message'])
            
            if response_json["error_code"] == 'LLMOverloadedError':
                raise LLMOverloadedError(response_json['message'])

            if response_json["error_code"] == 'MissingResource':
                raise MissingResource(response_json['message'])

        return response_json


    def get_plain_source_tree(self, plain_source, loaded_templates):
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
        headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        }
        
        payload = {
            "plain_source": plain_source,
            "loaded_templates": loaded_templates
        }
        
        return self.post_request(endpoint_url, headers, payload)


    def render_functional_requirement(self, frid, plain_source_tree, linked_resources, existing_files_content):
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
        headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        }
        
        payload = {
            "frid": frid,
            "plain_source_tree": plain_source_tree,
            "linked_resources": linked_resources,
            "existing_files_content": existing_files_content
        }

        return self.post_request(endpoint_url, headers, payload)


    def fix_unittests_issue(self, frid, plain_source_tree, linked_resources, existing_files_content, unittests_issue):
        endpoint_url = f"{self.api_url}/fix_unittests_issue"
        headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        }
        
        payload = {
            "frid": frid,
            "plain_source_tree": plain_source_tree,
            "linked_resources": linked_resources,
            "existing_files_content": existing_files_content,
            "unittests_issue": unittests_issue
        }
        
        return self.post_request(endpoint_url, headers, payload)


    def refactor_source_files_if_needed(self, files_to_check, existing_files_content):
        endpoint_url = f"{self.api_url}/refactor_source_files_if_needed"
        headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        }
        
        payload = {
            "files_to_check": list(files_to_check),
            "existing_files_content": existing_files_content
        }

        return self.post_request(endpoint_url, headers, payload)


    def render_conformance_tests(self, frid, functional_requirement_id, plain_source_tree, linked_resources, existing_files_content):
        endpoint_url = f"{self.api_url}/render_conformance_tests"
        headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        }
        
        payload = {
            "frid": frid,
            "functional_requirement_id": functional_requirement_id,
            "plain_source_tree": plain_source_tree,
            "linked_resources": linked_resources,
            "existing_files_content": existing_files_content
        }
        
        return self.post_request(endpoint_url, headers, payload)


    def generate_folder_name_from_functional_requirement(self, functional_requirement, existing_folder_names):
        endpoint_url = f"{self.api_url}/generate_folder_name_from_functional_requirement"
        headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        }
        
        payload = {
            "functional_requirement": functional_requirement,
            "existing_folder_names": existing_folder_names
        }
        
        return self.post_request(endpoint_url, headers, payload)


    def fix_conformance_tests_issue(self, frid, functional_requirement_id, plain_source_tree, linked_resources, existing_files_content, code_diff, conformance_tests_files, conformance_tests_issue, implementation_fix_count):
        endpoint_url = f"{self.api_url}/fix_conformance_tests_issue"
        headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        }
        
        payload = {
            "frid": frid,
            "functional_requirement_id": functional_requirement_id,
            "plain_source_tree": plain_source_tree,
            "linked_resources": linked_resources,
            "existing_files_content": existing_files_content,
            "code_diff": code_diff,
            "conformance_tests_files": conformance_tests_files,
            "conformance_tests_issue": conformance_tests_issue,
            "implementation_fix_count": implementation_fix_count
        }
        
        return self.post_request(endpoint_url, headers, payload)
