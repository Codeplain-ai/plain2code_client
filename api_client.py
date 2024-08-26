import os
import sys
import logging
import requests

logger = logging.getLogger(__name__)

class ApiClient:
    def __init__(self):
        self.api_key = self.get_api_key()

    @staticmethod
    def get_api_key():
        """Retrieve the API key from the environment variable."""
        api_key = os.environ.get('CLAUDE_API_KEY')
        if not api_key:
            logger.error("API key not found. Please set the CLAUDE_API_KEY environment variable.")
            sys.exit(1)
        return api_key

    def get_plain_sections(self, plain_source):
        """Get Plain Sections from The Plain Source using the API."""
        api_url = "https://api.codeplain.ai/plain_sections"
        headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        }
        
        try:
            with open(plain_source, 'r') as file:
                plain_source_content = file.read()
        except IOError as e:
            logger.error(f"Error reading The Plain Source file: {str(e)}")
            sys.exit(1)
        
        payload = {"plain_source": plain_source_content}
        
        try:
            response = requests.post(api_url, headers=headers, json=payload)
            response.raise_for_status()
            sections = response.json()
            logger.info("Successfully retrieved Plain Sections from the API")
            return sections
        except requests.exceptions.RequestException as e:
            logger.error(f"Error calling the API: {str(e)}")
            sys.exit(1)

    def render_functional_requirement(self, plain_sections, existing_files, frid=1):
        """Render the functional requirement using the API."""
        api_url = "https://api.codeplain.ai/render_functional_requirement"
        headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        }
        
        payload = {
            "frid": frid,
            "plain_sections": plain_sections,
            "existing_files_content": existing_files
        }
        
        try:
            response = requests.post(api_url, headers=headers, json=payload)
            response.raise_for_status()
            rendered_files = response.json()
            logger.info(f"Successfully rendered functional requirement {frid}")
            return rendered_files
        except requests.exceptions.RequestException as e:
            logger.error(f"Error calling the render_functional_requirement API: {str(e)}")
            sys.exit(1)
    def get_total_functional_requirements(self, plain_sections):
        """Get the total number of functional requirements."""
        return len(plain_sections.get("Functional Requirements:", []))
    def fix_unittest_issues(self, plain_sections, existing_files, frid, build_folder):
        """Fix unittest issues using the API."""
        api_url = "https://api.codeplain.ai/fix_unittests_issue"
        headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        }
        
        with open(os.path.join(build_folder, "test_output.txt"), "r") as f:
            unittests_issue = f.read()
        
        payload = {
            "frid": frid,
            "plain_sections": plain_sections,
            "existing_files_content": existing_files,
            "unittests_issue": unittests_issue
        }
        
        response = requests.post(api_url, headers=headers, json=payload)
        response.raise_for_status()
        fixed_files = response.json()
        return fixed_files