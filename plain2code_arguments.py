import argparse
import os
import re

from plain2code_console import console

CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
DEFAULT_BUILD_FOLDER = "build"
DEFAULT_CONFORMANCE_TESTS_FOLDER = "conformance_tests"


def non_empty_string(s):
    if not s:
        raise argparse.ArgumentTypeError("The string cannot be empty.")
    return s


def frid_string(s):
    """Validate that the string contains only numbers separated by dots."""
    if not s:
        raise argparse.ArgumentTypeError("The functional requirement ID cannot be empty.")

    if not re.match(r"^\d+(\.\d+)*$", s):
        raise argparse.ArgumentTypeError(
            "Functional requirement ID string must contain only numbers optionally separated by dots (e.g. '1', '1.2.3')"
        )
    return s


def frid_range_string(s):
    """Validate that the string contains two frids separated by comma."""
    if not s:
        raise argparse.ArgumentTypeError("The range cannot be empty.")

    parts = s.split(",")
    if len(parts) > 2:
        raise argparse.ArgumentTypeError("Range must contain at most two functional requirement IDs separated by comma")

    for part in parts:
        frid_string(part)

    return s


def parse_arguments():
    parser = argparse.ArgumentParser(description="Render plain code to target code.")

    parser.add_argument("filename", type=str, help="plain file to render")
    parser.add_argument("--verbose", "-v", action="store_true", help="enable verbose output")
    parser.add_argument("--debug", action="store_true", help="enable debug information")
    parser.add_argument("--base-folder", type=str, help="base folder for the build files")
    parser.add_argument(
        "--build-folder", type=non_empty_string, default=DEFAULT_BUILD_FOLDER, help="folder for build files"
    )

    render_range_group = parser.add_mutually_exclusive_group()
    render_range_group.add_argument(
        "--render-range", type=frid_range_string, help="which functional requirements should be generated"
    )
    render_range_group.add_argument(
        "--render-from", type=frid_string, help="from which functional requirements generation should be continued"
    )

    parser.add_argument("--unittests-script", type=str, help="a script to run unit tests")
    parser.add_argument(
        "--conformance-tests-folder",
        type=non_empty_string,
        default=DEFAULT_CONFORMANCE_TESTS_FOLDER,
        help="folder for conformance test files",
    )
    parser.add_argument("--conformance-tests-script", type=str, help="a script to run conformance tests")
    parser.add_argument(
        "--api", type=str, nargs="?", const="https://api.codeplain.ai", help="force using the API (for internal use)"
    )
    parser.add_argument(
        "--api-key",
        type=str,
        default=CLAUDE_API_KEY,
        help="API key used to access the API. If not provided, the CLAUDE_API_KEY environment variable is used.",
    )
    parser.add_argument("--full-plain", action="store_true", help="emit full plain text to render")
    parser.add_argument(
        "--dry-run", action="store_true", help="preview what plain2code would do without actually making any changes"
    )

    args = parser.parse_args()

    # Validate API key
    if not args.api_key or args.api_key == "":
        console.error(
            "Error: API key is not provided. Please provide an API key using the --api-key flag or by setting the CLAUDE_API_KEY environment variable."
        )
        exit(1)

    return args
