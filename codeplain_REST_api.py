import json
import requests


class FunctionalRequirementTooComplex(Exception):
    pass


class ConflictingRequirements(Exception):
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


    def get_plain_sections(self, plain_source):
        """
        Extracts labeled sections from the given plain text source in Markdown format.

        Args:
            plain_source (str): A string containing the plain text source to be parsed. 
                                The input must be in Markdown format and include the following 
                                mandatory labeled sections, each marked by a specific label 
                                at the start of the line:
                                
                                - "***Definitions:***"
                                - "***Functional Requirements:***"
                                - "***Non-Functional Requirements:***"
                                
                                Other labeled sections, such as "***Test Requirements:***", 
                                are optional but will be parsed if present. The input should be 
                                non-empty and formatted using consistent Markdown syntax with 
                                the required labels to ensure successful parsing and extraction.

        Returns:
            list: A list of labeled sections extracted from the plain source. Each section is 
                a structured segment within the source text, starting with a recognized 
                labeled header followed by its content.

        Raises:
            Exception: If parsing of plain_source fails.

        Notes:
            This method processes the input text using predefined parsing rules to identify 
            and extract labeled sections. The document must be formatted correctly in Markdown, 
            with specific labels (e.g., "***Definitions:***") marking the start of each segment. 
            The "Definitions," "Functional Requirements," and "Non-Functional Requirements" 
            labeled sections are required, while others are optional.
        """
        api_url = f"{self.api_url}/plain_sections"
        headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        }
        
        payload = {"plain_source": plain_source}
        
        response = requests.post(api_url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()


    def render_functional_requirement(self, frid, plain_sections, existing_files_content):
        """
        Renders the content of a functional requirement based on the provided ID, 
        corresponding sections from a Plain document, and existing files' content.

        Args:
            frid (str): The unique identifier for the functional requirement to be rendered.
            plain_sections (list of str): A list of sections from the Plain document that 
                                        are relevant to the functional requirement.
            existing_files_content (dict): A dictionary where the keys represent filenames 
                                        and the values are the content of those files, 
                                        used to cross-reference or augment the rendering 
                                        of the functional requirement.

        Returns:
            str: A string containing the rendered functional requirement, formatted 
                appropriately based on the inputs.

        Raises:
            ValueError: If the frid is invalid or the necessary sections cannot be found.
        """
        api_url = f"{self.api_url}/render_functional_requirement"
        headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        }
        
        payload = {
            "frid": frid,
            "plain_sections": plain_sections,
            "existing_files_content": existing_files_content
        }
        
        response = requests.post(api_url, headers=headers, json=payload)

        response_json = response.json()
        if response.status_code == requests.codes.bad_request:
            
            if response_json["error_code"] == 'FunctionalRequirementTooComplex':
                raise FunctionalRequirementTooComplex(response_json['message'])

        response.raise_for_status()

        return response_json  


    def fix_unittests_issue(self, frid, plain_sections, existing_files_content, unittests_issue):
        api_url = f"{self.api_url}/fix_unittests_issue"
        headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        }
        
        payload = {
            "frid": frid,
            "plain_sections": plain_sections,
            "existing_files_content": existing_files_content,
            "unittests_issue": unittests_issue
        }
        
        response = requests.post(api_url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()


    def refactor_source_files_if_needed(self, files_to_check, existing_files_content):
        api_url = f"{self.api_url}/refactor_source_files_if_needed"
        headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        }
        
        payload = {
            "files_to_check": list(files_to_check),
            "existing_files_content": existing_files_content
        }

        response = requests.post(api_url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()


    def render_e2e_tests(self, frid, plain_sections, existing_files_content):
        api_url = f"{self.api_url}/render_e2e_tests"
        headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        }
        
        payload = {
            "frid": frid,
            "plain_sections": plain_sections,
            "existing_files_content": existing_files_content
        }
        
        response = requests.post(api_url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()


    def generate_folder_name_from_functional_requirement(self, functional_requirement, existing_folder_names):
        api_url = f"{self.api_url}/generate_folder_name_from_functional_requirement"
        headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        }
        
        payload = {
            "functional_requirement": functional_requirement,
            "existing_folder_names": existing_folder_names
        }
        
        response = requests.post(api_url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()


    def fix_e2e_tests_issue(self, frid, functional_requirement_id, plain_sections, existing_files_content, code_diff, e2e_tests_files, e2e_tests_issue, implementation_fix_count):
        api_url = f"{self.api_url}/fix_e2e_tests_issue"
        headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        }
        
        payload = {
            "frid": frid,
            "functional_requirement_id": functional_requirement_id,
            "plain_sections": plain_sections,
            "existing_files_content": existing_files_content,
            "code_diff": code_diff,
            "e2e_tests_files": e2e_tests_files,
            "e2e_tests_issue": e2e_tests_issue,
            "implementation_fix_count": implementation_fix_count
        }
        
        response = requests.post(api_url, headers=headers, json=payload)

        response_json = response.json()
        if response.status_code == requests.codes.bad_request:
            
            if response_json["error_code"] == 'ConflictingRequirements':
                raise ConflictingRequirements(response_json['message'])

        response.raise_for_status()

        return response_json
