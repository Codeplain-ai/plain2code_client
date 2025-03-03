#!/bin/bash

# Check if build folder name is provided
if [ -z "$1" ]; then
  printf "Error: No build folder name provided.\n"
  printf "Usage: $0 <build_folder_name> <conformance_tests_folder>\n"
  exit 1
fi

# Check if conformance tests folder name is provided
if [ -z "$2" ]; then
  printf "Error: No conformance tests folder name provided.\n"
  printf "Usage: $0 <build_folder_name> <conformance_tests_folder>\n"
  exit 1
fi

current_dir=$(pwd)

# Move to the subfolder
cd "$1" 2>/dev/null

if [ $? -ne 0 ]; then
  printf "Error: Build folder '$1' does not exist.\n"
  exit 2
fi

# Execute all Python conformance tests in the build folder
printf "Running Python conformance tests...\n\n"

output=$(python -m unittest discover -b -s "$current_dir/$2" 2>&1)
exit_code=$?

# Echo the original output
echo "$output"

# Check if no tests were discovered
if echo "$output" | grep -q "Ran 0 tests in"; then
    printf "\nError: No unittests discovered.\n"
    exit 1
fi

# Echo the original exit code of the unittest command
exit $exit_code