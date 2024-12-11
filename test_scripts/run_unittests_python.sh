#!/bin/bash

# Check if subfolder name is provided
if [ -z "$1" ]; then
  echo "Error: No subfolder name provided."
  echo "Usage: $0 <subfolder_name>"
  exit 1
fi

# Move to the subfolder
cd "$1" 2>/dev/null

if [ $? -ne 0 ]; then
  echo "Error: Subfolder '$1' does not exist."
  exit 2
fi

# Execute all Python unittests in the subfolder
echo "Running Python unittests in $1..."

output=$(timeout 60s python -m unittest discover -b 2>&1)
exit_code=$?

# Check if the command timed out
if [ $exit_code -eq 124 ]; then
    printf "\nError: Unittests timed out after 60 seconds.\n"
    exit 3
fi

# Echo the original output
echo "$output"

# Return the exit code of the unittest command
exit $exit_code

# Note: The 'discover' option automatically identifies and runs all unittests in the current directory and subdirectories
# Ensure that your Python files are named according to the unittest discovery pattern (test*.py by default)
