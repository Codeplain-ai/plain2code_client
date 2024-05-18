import os
import argparse
import logging
import requests
import shutil
import subprocess

API_BASE_URL = "https://api.codeplain.ai"
MAX_FIX_ATTEMPTS = 5

def get_plain_sections(api_key, plain_text):
    url = f"{API_BASE_URL}/plain_sections"
    headers = {"X-API-KEY": api_key}
    payload = {"plain_text": plain_text}
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error getting plain sections: {e}")
        raise

def render_functional_requirement(api_key, frid, plain_sections, existing_files):
    url = f"{API_BASE_URL}/render_functional_requirement"
    headers = {"X-API-KEY": api_key}
    payload = {
        "frid": frid,
        "plain_sections": plain_sections,
        "existing_files_content": existing_files
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status() 
        return response.json()["files"]
    except requests.exceptions.RequestException as e:
        logging.error(f"Error rendering functional requirement {frid}: {e}")
        raise

def fix_unittests_issue(api_key, frid, plain_sections, existing_files, unittests_issue):
    url = f"{API_BASE_URL}/fix_unittests_issue"
    headers = {"X-API-KEY": api_key}
    payload = {
        "frid": frid,
        "plain_sections": plain_sections,
        "existing_files_content": existing_files,
        "unittests_issue": unittests_issue
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()["files"]
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fixing unit tests issue for functional requirement {frid}: {e}")
        raise

def clear_build_folder(build_folder):
    if os.path.exists(build_folder):
        for filename in os.listdir(build_folder):
            file_path = os.path.join(build_folder, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                logging.error(f"Failed to delete {file_path}. Reason: {e}")
    else:
        os.makedirs(build_folder)

def copy_base_files(base_folder, build_folder):
    if not os.path.exists(base_folder):
        raise ValueError(f"Base folder {base_folder} does not exist")
    
    try:
        shutil.copytree(base_folder, build_folder, dirs_exist_ok=True)
        logging.info(f"Copied files from base folder {base_folder} to build folder {build_folder}")
    except Exception as e:
        logging.error(f"Error copying files from base folder {base_folder} to build folder {build_folder}: {e}")
        raise

def run_unit_tests(unit_test_script, build_folder):
    if not os.path.isfile(unit_test_script):
        raise ValueError(f"Unit test script {unit_test_script} does not exist")
    if not os.access(unit_test_script, os.X_OK):
        raise ValueError(f"Unit test script {unit_test_script} is not executable")

    try:
        result = subprocess.run([unit_test_script, build_folder], capture_output=True, text=True)
        print(result.stdout)
        return result.returncode, result.stderr
    except Exception as e:
        logging.error(f"Error running unit tests: {e}")
        raise

def main():
    parser = argparse.ArgumentParser(description="Render code from plain text using the Codeplain API")
    parser.add_argument("plain_source", help="Path to The Plain Source file")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument("-b", "--build-folder", default="build", help="Path to The Build Folder (default: build)")
    parser.add_argument("-s", "--base-folder", help="Path to The Base Folder containing files to copy verbatim to the build folder")
    parser.add_argument("-t", "--unit-test-script", help="Path to shell script for running unit tests")
    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.INFO)
    else:
        logging.basicConfig(level=logging.WARN)
    
    logging.info(f"Verbose output enabled: {args.verbose}")
    logging.info(f"Build folder: {args.build_folder}")

    clear_build_folder(args.build_folder)

    if args.base_folder:
        logging.info(f"Base folder: {args.base_folder}")
        copy_base_files(args.base_folder, args.build_folder)

    api_key = os.environ.get("CLAUDE_API_KEY")
    if not api_key:
        raise ValueError("CLAUDE_API_KEY environment variable is not set")

    with open(args.plain_source, "r") as f:
        plain_text = f.read()

    logging.info(f"Getting plain sections from {args.plain_source}...")
    plain_sections = get_plain_sections(api_key, plain_text)
    logging.info(f"Got {len(plain_sections['Functional Requirements:'])} functional requirements")
    
    plain_source_name = os.path.basename(args.plain_source)
    print(f"Rendering {plain_source_name} to target code.")
    
    if args.verbose:
        print('\n"Definitions:"\n' + plain_sections["Definitions:"])
        print('\n"Non-Functional Requirements:"\n' + plain_sections["Non-Functional Requirements:"])
    
    existing_files = {}

    for i, fr_text in enumerate(plain_sections["Functional Requirements:"], start=1):
        logging.info(f"Rendering functional requirement {i}...")
        rendered_files = render_functional_requirement(api_key, i, plain_sections, existing_files)
        
        for filename, content in rendered_files.items():
            file_path = os.path.join(args.build_folder, filename)
            logging.info(f"Writing file {file_path}...")
            with open(file_path, "w") as f:
                f.write(content)
        
        existing_files = rendered_files
        logging.info(f"Rendered {len(rendered_files)} files for functional requirement {i}")

        if args.unit_test_script:
            logging.info(f"Running unit tests with script {args.unit_test_script}...")
            returncode, stderr = run_unit_tests(args.unit_test_script, args.build_folder)
            
            fix_attempts = 0
            while returncode != 0:
                if fix_attempts >= MAX_FIX_ATTEMPTS:
                    logging.error(f"Unit tests still failing after {MAX_FIX_ATTEMPTS} fix attempts. Terminating.")
                    logging.error(f"Last error output from unit tests:\n{stderr}")
                    exit(1)

                logging.warning(f"Unit tests failed on attempt {fix_attempts+1}. Attempting to fix...")
                fixed_files = fix_unittests_issue(api_key, i, plain_sections, existing_files, stderr)

                for filename, content in fixed_files.items():
                    file_path = os.path.join(args.build_folder, filename)
                    logging.info(f"Writing fixed file {file_path}...")
                    with open(file_path, "w") as f:
                        f.write(content)

                existing_files = fixed_files
                returncode, stderr = run_unit_tests(args.unit_test_script, args.build_folder)
                fix_attempts += 1

            logging.info("Unit tests passed")

if __name__ == "__main__":
    main()