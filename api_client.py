import requests
import json
import os

def get_api_key():
    api_key = os.environ.get('CLAUDE_API_KEY')
    if not api_key:
        raise ValueError("CLAUDE_API_KEY environment variable is not set")
    return api_key

def get_plain_sections(api_key, plain_text):
    url = "https://api.codeplain.ai/plain_sections"
    headers = {
        "X-API-KEY": api_key,
        "Content-Type": "application/json"
    }
    payload = {
        "plain_text": plain_text
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        raise RuntimeError(f"Error calling plain_sections API: {str(e)}") from e
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Error decoding API response: {str(e)}") from e
    except Exception as e:
        raise RuntimeError(f"Unexpected error in get_plain_sections: {str(e)}") from e

def render_functional_requirement(api_key, frid, plain_sections, existing_files):
    url = "https://api.codeplain.ai/render_functional_requirement"
    headers = {
        "X-API-KEY": api_key,
        "Content-Type": "application/json"
    }
    payload = {
        "frid": frid,
        "plain_sections": plain_sections,
        "existing_files_content": existing_files
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        raise RuntimeError(f"Error calling render_functional_requirement API: {str(e)}") from e

def fix_unittests_issue(api_key, frid, sections, existing_files, error_message):
    url = "https://api.codeplain.ai/fix_unittests_issue"
    headers = {
        "X-API-KEY": api_key,
        "Content-Type": "application/json"
    }
    payload = {
        "frid": frid,
        "plain_sections": sections,
        "existing_files_content": existing_files,
        "unittests_issue": error_message
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        raise RuntimeError(f"Error calling fix_unittests_issue API: {str(e)}") from e
    except Exception as e:
        raise RuntimeError(f"Unexpected error in fix_unittests_issue: {str(e)}") from e