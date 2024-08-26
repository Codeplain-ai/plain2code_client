#!/usr/bin/env python3
import argparse
import logging
import os
import sys
import subprocess
from api_client import ApiClient
from file_operations import (
    create_build_folder,
    clear_build_folder,
    copy_base_files,
    load_existing_files,
    write_rendered_files
)

# Set up logging
logging.basicConfig(level=logging.WARN, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_unit_tests(test_script, build_folder):
    """Run the specified unit test script with the build folder as its parameter."""
    try:
        result = subprocess.run([test_script, build_folder], capture_output=True, text=True, check=True)
        logger.info("Unit tests completed successfully.")
        logger.info(f"Test output:\n{result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Unit tests failed with exit code {e.returncode}")
        logger.error(f"Test output:\n{e.stdout}")
        logger.error(f"Test error:\n{e.stderr}")
        return False
    except Exception as e:
        logger.error(f"Error running unit tests: {str(e)}")
        sys.exit(1)

def display_rendering_progress(frid, requirement_description):
    """Display the rendering progress for each functional requirement."""
    ordinal = lambda n: "%d%s" % (n,"tsnrhtdd"[(n//10%10!=1)*(n%10<4)*n%10::4])
    print(f"\nRendering {ordinal(frid)} functional requirement:")
    print(requirement_description)

def get_requirement_description(sections, frid):
    """Get the description of a specific functional requirement."""
    return sections.get("Functional Requirements:", [])[frid - 1] if frid <= len(sections.get("Functional Requirements:", [])) else ""

def render_all_requirements(api_client, sections, existing_files, build_folder, test_script):
    """Render all functional requirements and run tests after each."""
    total_requirements = api_client.get_total_functional_requirements(sections)
    for frid in range(1, total_requirements + 1):
        try:
            rendered_files = api_client.render_functional_requirement(sections, existing_files, frid)
            requirement_description = get_requirement_description(sections, frid)
            display_rendering_progress(frid, requirement_description)
            write_rendered_files(build_folder, rendered_files)
            logger.info(f"Rendered functional requirement {frid}")
            if test_script:
                tests_passed = run_unit_tests(test_script, build_folder)
                if not tests_passed:
                    fix_attempts = 0
                    while not tests_passed and fix_attempts < 5:
                        logger.info(f"Attempting to fix unit test issues (attempt {fix_attempts + 1})")
                        fix_result = api_client.fix_unittest_issues(sections, existing_files, frid, build_folder)
                        write_rendered_files(build_folder, fix_result)
                        tests_passed = run_unit_tests(test_script, build_folder)
                        fix_attempts += 1
                    
                    if not tests_passed:
                        logger.error("Failed to fix unit test issues after 5 attempts. Terminating the app.")
                        sys.exit(1)
            existing_files = load_existing_files(build_folder)
        except Exception as e:
            logger.error(f"Error rendering functional requirement {frid}: {str(e)}")
            sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Plain2Code: Convert plain text to software code.")
    parser.add_argument('plain_source', help="Path to The Plain Source file.")
    parser.add_argument('-v', '--verbose', action='store_true', help="Enable verbose output.")
    parser.add_argument('-V', '--version', action='version', version='%(prog)s 1.0')
    parser.add_argument('-b', '--build-folder', default='build',
                        help="Specify the location of the build folder (default: build)")
    parser.add_argument('-B', '--base-folder',
                        help="Specify the location of the base folder containing files to be copied to the build folder")
    parser.add_argument('-t', '--test-script',
                        help="Specify a shell script to run unit tests. The script will receive the build folder as its parameter.")

    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.INFO)

    try:
        logger.info("Starting Plain2Code conversion process.")
        api_client = ApiClient()
        clear_build_folder(args.build_folder)
        if args.base_folder:
            copy_base_files(args.base_folder, args.build_folder)

        existing_files = load_existing_files(args.build_folder)
        logger.info(f"Loaded {len(existing_files)} existing files from the build folder.")

        sections = api_client.get_plain_sections(args.plain_source)
        print(f"Rendering {args.plain_source} to software code.")

        logger.info(f"The Plain Source file: {args.plain_source}")
        
        render_all_requirements(api_client, sections, existing_files, args.build_folder, args.test_script)

        if args.test_script:
            run_unit_tests(args.test_script, args.build_folder)
        
        print("\nRendering finished!")
        logger.info("Plain2Code conversion process completed successfully.")

    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        logger.debug("Exception details:", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()