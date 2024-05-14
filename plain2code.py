import argparse
import logging
import os
import shutil
import requests
import subprocess

API_URL = "https://api.codeplain.ai"

def get_plain_sections(plain_source):
    """
    Get plain sections from the API.

    Args:
        plain_source (str): Plain source content

    Returns:
        dict: Plain sections
    """
    try:
        response = requests.post(f"{API_URL}/plain_sections", json={"plain_source": plain_source})
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error getting plain sections from API. Error: {str(e)}")
        raise

def load_existing_files(build_folder):
    """
    Load the content of all existing files in the build folder.

    Args:
        build_folder (str): Path to the build folder

    Returns:
        dict: Dictionary containing the content of all existing files
    """
    existing_files = {}
    for root, _, files in os.walk(build_folder):
        for file in files:
            file_path = os.path.join(root, file)
            with open(file_path, 'r') as f:
                content = f.read()
                relative_path = os.path.relpath(file_path, build_folder)
                existing_files[relative_path] = content
    return existing_files

def render_functional_requirement(frid, plain_sections, existing_files):
    """
    Render a functional requirement using the API.

    Args:
        frid (int): Functional requirement ID
        plain_sections (dict): Plain sections dictionary
        existing_files (dict): Dictionary containing the content of existing files

    Returns:
        dict: Dictionary containing the rendered files
    """
    try:
        response = requests.post(f"{API_URL}/render_functional_requirement", json={
            "frid": frid,
            "plain_sections": plain_sections,
            "existing_files_content": existing_files
        })
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error rendering functional requirement {frid} from API. Error: {str(e)}")
        raise

def save_rendered_files(rendered_files, build_folder):
    """
    Save the rendered files to the build folder.

    Args:
        rendered_files (dict): Dictionary containing the rendered files
        build_folder (str): Path to the build folder
    """
    for file_path, content in rendered_files.items():
        full_path = os.path.join(build_folder, file_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, 'w') as f:
            f.write(content)
        logging.debug(f"Saved rendered file: {file_path}")

def run_test_script(test_script, build_folder):
    """
    Run the test script with the build folder as an argument.

    Args:
        test_script (str): Path to the test script
        build_folder (str): Path to the build folder

    Returns:
        tuple: A tuple containing the exit code and output of the test script
    """
    try:
        result = subprocess.run([test_script, build_folder], capture_output=True, text=True)
        return result.returncode, result.stdout
    except FileNotFoundError as e:
        logging.error(f"Test script not found: {test_script}. Error: {str(e)}")
        return 1, ""
    except Exception as e:
        logging.error(f"Error running test script: {test_script}. Error: {str(e)}")
        return 1, ""

def main():
    """
    Codeplain - Plain Code to Software Code Converter

    Args:
        plain_source_file (str): Plain source file name
        -v, --verbose (bool): Enable verbose output
        -b BUILD_FOLDER, --build-folder BUILD_FOLDER (str): Location of the build folder (default: 'build')
        -s BASE_FOLDER, --source-folder BASE_FOLDER (str): Location of the base folder (default: None)
        -t TEST_SCRIPT, --test-script TEST_SCRIPT (str): Path to the shell script for running unit tests (default: None)
    """
    parser = argparse.ArgumentParser(description='Codeplain - Plain Code to Software Code Converter')
    parser.add_argument('plain_source_file', help='Plain source file name')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output')
    parser.add_argument('-b', '--build-folder', default='build', help='Location of the build folder (default: \'build\')')
    parser.add_argument('-s', '--source-folder', default=None, help='Location of the base folder (default: None)')
    parser.add_argument('-t', '--test-script', default=None, help='Path to the shell script for running unit tests (default: None)')

    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.WARN)

    logging.debug(f"Running with arguments: {args}")

    try:
        with open(args.plain_source_file, 'r') as file:
            plain_source = file.read()
        logging.debug(f"Read {len(plain_source)} characters from {args.plain_source_file}")
    except FileNotFoundError as e:
        logging.error(f"Plain source file not found: {args.plain_source_file}. Error: {str(e)}")
        return
    except Exception as e:
        logging.error(f"Error reading plain source file: {args.plain_source_file}. Error: {str(e)}")
        return
    
    if os.path.exists(args.build_folder):
        try:
            shutil.rmtree(args.build_folder)
            logging.debug(f"Deleted existing build folder: {args.build_folder}")
        except Exception as e:
            logging.error(f"Error deleting existing build folder: {args.build_folder}. Error: {str(e)}")
            return
    
    os.makedirs(args.build_folder)
    logging.debug(f"Created build folder: {args.build_folder}")
        
    if args.source_folder:
        if not os.path.exists(args.source_folder):
            logging.error(f"Base folder not found: {args.source_folder}")
            return
        
        try:
            shutil.copytree(args.source_folder, args.build_folder, dirs_exist_ok=True)
            logging.debug(f"Copied files from base folder: {args.source_folder} to build folder: {args.build_folder}")
        except Exception as e:
            logging.error(f"Error copying files from base folder: {args.source_folder} to build folder: {args.build_folder}. Error: {str(e)}")
            return

    try:
        plain_sections = get_plain_sections(plain_source)
        logging.debug(f"Got plain sections: {plain_sections}")
    except Exception as e:
        logging.error(f"Error getting plain sections. Error: {str(e)}")
        return

    print(f"Rendering {args.plain_source_file} to target code.")
    
    if args.verbose:
        print("Definitions:")
        print(plain_sections["Definitions:"])
        print("Non-Functional Requirements:")
        print(plain_sections["Non-Functional Requirements:"])

    existing_files = load_existing_files(args.build_folder)
    logging.debug(f"Loaded existing files: {existing_files}")

    functional_requirements = plain_sections["Functional Requirements:"]
    for frid, requirement in enumerate(functional_requirements, start=1):
        try:
            rendered_files = render_functional_requirement(frid, plain_sections, existing_files)
            save_rendered_files(rendered_files, args.build_folder)
            existing_files.update(rendered_files)
            logging.info(f"Rendered functional requirement {frid}: {requirement}")
        except Exception as e:
            logging.error(f"Error rendering functional requirement {frid}. Error: {str(e)}")
            return

        if args.test_script:
            exit_code, output = run_test_script(args.test_script, args.build_folder)
            print(f"Test script output for requirement {frid}:\n{output}")
            if exit_code != 0:
                logging.error(f"Test script failed for requirement {frid} with exit code: {exit_code}")
                return exit_code

    print("All functional requirements rendered successfully.")

if __name__ == '__main__':
    main()