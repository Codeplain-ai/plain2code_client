#!/usr/bin/env python3
import argparse
import logging
import sys
import subprocess
import json
from api_client import get_api_key, get_plain_sections, render_functional_requirement, fix_unittests_issue
from file_operations import read_plain_source, ensure_build_folder, clear_build_folder, copy_base_folder, load_existing_files, update_build_folder
from logging_setup import setup_logging

def run_unit_tests(test_script, build_folder, logger):
    if test_script:
        try:
            result = subprocess.run([test_script, build_folder], check=True, capture_output=True, text=True)
            logger.info(f"Unit tests completed successfully. Output:\n{result.stdout}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Unit tests failed. Error output:\n{e.stderr}")
            raise RuntimeError("Unit tests failed") from e
        except Exception as e:
            logger.error(f"Error running unit tests: {str(e)}")
            raise RuntimeError(f"Error running unit tests: {str(e)}") from e

def render_and_test_functional_requirements(api_key, sections, existing_files, build_folder, test_script, logger, input_file):
    print(f"Rendering {input_file} to software code.\n")
    for frid, requirement in enumerate(sections.get('Functional Requirements:', []), start=1):
        logger.info(f"Rendering functional requirement {frid}: {requirement}")
        print(f"Rendering {frid}{'st' if frid == 1 else 'nd' if frid == 2 else 'th'} functional requirement:")
        print(f"{requirement}\n")
        try:
            rendered_files = render_functional_requirement(api_key, frid, sections, existing_files)
            update_build_folder(build_folder, rendered_files)
            existing_files.update(rendered_files.get('files', {}))
            
            attempts = 0
            while attempts < 5:
                try:
                    run_unit_tests(test_script, build_folder, logger)
                    logger.info(f"Successfully rendered and tested requirement {frid}")
                    break
                except RuntimeError as e:
                    attempts += 1
                    if attempts == 5:
                        logger.error(f"Failed to fix unit test issues after 5 attempts for requirement {frid}")
                        raise
                    logger.warning(f"Attempt {attempts}: Fixing unit test issues for requirement {frid}")
                    fix_result = fix_unittests_issue(api_key, frid, sections, existing_files, str(e))
                    update_build_folder(build_folder, fix_result)
                    existing_files.update(fix_result.get('files', {}))
        except RuntimeError as e:
            logger.error(f"Error processing requirement {frid}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error processing requirement {frid}: {str(e)}")
    print("Rendering finished!")

def main(args):
    logger = setup_logging(args.verbose)
    
    try:
        api_key = get_api_key()
        
        build_folder = ensure_build_folder(args.build_folder)
        logger.info(f"Using build folder: {build_folder}")

        clear_build_folder(build_folder)
        logger.info(f"Cleared The Build Folder: {build_folder}")

        copy_base_folder(args.base_folder, build_folder)
        
        plain_source_content = read_plain_source(args.input)
        logger.info(f"Successfully read The Plain Source file: {args.input}")
        logger.debug(f"Plain source content: {plain_source_content[:100]}...")  # Debug log example
        
        existing_files = load_existing_files(build_folder)
        logger.info(f"Loaded {len(existing_files)} existing files from The Build Folder")
        logger.debug(f"Existing files: {json.dumps(list(existing_files.keys()), indent=2)}")
        
        sections = get_plain_sections(api_key, plain_source_content)
        logger.info("Successfully retrieved Plain Sections from the API")
        logger.debug(f"Received sections: {json.dumps(sections, indent=2)}")
        
        render_and_test_functional_requirements(api_key, sections, existing_files, build_folder, args.unit_test_script, logger, args.input)
        
        logger.info("Application executed successfully")
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Plain2Code: Render plain code to software code")
    parser.add_argument('input', help='The Plain Source file name')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output')
    parser.add_argument('-b', '--build-folder', default='build', help='Specify the location of the build folder (default: build)')
    parser.add_argument('--base-folder', help='Specify the location of the base folder to be copied to the build folder')
    parser.add_argument('--unit-test-script', help='Specify a shell script to run unit tests')
    args = parser.parse_args()
    
    main(args)