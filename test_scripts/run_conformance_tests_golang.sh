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

GO_BUILD_SUBFOLDER=go_$1

if [ "${VERBOSE:-}" -eq 1 ] 2>/dev/null; then
  printf "Preparing Go build subfolder: $GO_BUILD_SUBFOLDER\n"
fi

# Check if the go build subfolder exists
if [ -d "$GO_BUILD_SUBFOLDER" ]; then
  # Find and delete all files and folders
  find "$GO_BUILD_SUBFOLDER" -mindepth 1 -exec rm -rf {} +
  
  if [ "${VERBOSE:-}" -eq 1 ] 2>/dev/null; then
    printf "Cleanup completed.\n"
  fi
else
  if [ "${VERBOSE:-}" -eq 1 ] 2>/dev/null; then
    printf "Subfolder does not exist. Creating it...\n"
  fi

  mkdir $GO_BUILD_SUBFOLDER
fi

cp -R $1/* $GO_BUILD_SUBFOLDER

# Move to the subfolder
cd "$GO_BUILD_SUBFOLDER" 2>/dev/null

if [ $? -ne 0 ]; then
  printf "Error: Go build folder '$GO_BUILD_SUBFOLDER' does not exist.\n"
  exit 2
fi

echo "Runinng go get in the build folder..."
go get

cd "$current_dir/$2" 2>/dev/null

if [ $? -ne 0 ]; then
  printf "Error: Conformance tests folder '$current_dir/$2' does not exist.\n"
  exit 2
fi

echo "Checking for go.mod in conformance test directory..."
if [ -f "go.mod" ]; then
    echo "Running go get in conformance test directory..."
    go get
else
    echo "No go.mod found in conformance test directory, skipping go get"
fi

# Move back to build directory
cd "$current_dir/$GO_BUILD_SUBFOLDER" 2>/dev/null

# Execute Go lang conformance tests
printf "Running Golang conformance tests...\n\n"

output=$(go run $current_dir/$2/conformance_tests.go 2>&1)
exit_code=$?

# If there was an error, print the output and exit with the error code
if [ $exit_code -ne 0 ]; then
    echo "$output"
    exit $exit_code
fi

# Echo the original exit code of the unittest command
exit $exit_code