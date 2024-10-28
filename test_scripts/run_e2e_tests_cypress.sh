#!/bin/bash

NPM_INSTALL_OUTPUT_FILTER="up to date in|added [0-9]* packages, removed [0-9]* packages, and changed [0-9]* packages in|removed [0-9]* packages, and changed [0-9]* packages in|added [0-9]* packages in|removed [0-9]* packages in"

# Function to get all child processes of a given PID and store them in a list
get_children() {
    local parent_pid=$1
    local children=$(pgrep -P $parent_pid)

    for child in $children
    do
        # Add the child process to the list
        processes_to_kill+=($child)
        # Recursively find the children of the child process
        get_children $child
    done
}

# Check if build folder name is provided
if [ -z "$1" ]; then
  printf "Error: No build folder name provided.\n"
  printf "Usage: $0 <build_folder_name> <e2e_tests_folder>\n"
  exit 1
fi

# Check if e2e tests folder name is provided
if [ -z "$2" ]; then
  printf "Error: No e2e tests folder name provided.\n"
  printf "Usage: $0 <build_folder_name> <e2e_tests_folder>\n"
  exit 1
fi

if [[ "$3" == "-v" || "$3" == "--verbose" ]]; then
  VERBOSE=1
fi

current_dir=$(pwd)

# Ensures that if any command in the pipeline fails (like npm run build), the entire pipeline
# will return a non-zero status, allowing the if condition to properly catch failures.
set -o pipefail

# Running React application
printf "### Step 1: Starting the React application in folder $1...\n"

# Define the path to the subfolder
NODE_SUBFOLDER=node_$1

if [ "${VERBOSE:-}" -eq 1 ] 2>/dev/null; then
  printf "Preparing Node subfolder: $NODE_SUBFOLDER\n"
fi

# Check if the node subfolder exists
if [ -d "$NODE_SUBFOLDER" ]; then
  # Find and delete all files and folders except "node_modules", "build", and "package-lock.json"
  find "$NODE_SUBFOLDER" -mindepth 1 ! -path "$NODE_SUBFOLDER/node_modules*" ! -path "$NODE_SUBFOLDER/build*" ! -name "package-lock.json" -exec rm -rf {} +
  
  if [ "${VERBOSE:-}" -eq 1 ] 2>/dev/null; then
    printf "Cleanup completed, keeping 'node_modules' and 'package-lock.json'.\n"
  fi
else
  if [ "${VERBOSE:-}" -eq 1 ] 2>/dev/null; then
    printf "Subfolder does not exist. Creating it...\n"
  fi

  mkdir $NODE_SUBFOLDER
fi

cp -R $1/* $NODE_SUBFOLDER

# Move to the subfolder
cd "$NODE_SUBFOLDER" 2>/dev/null

if [ $? -ne 0 ]; then
  printf "Error: Node build folder '$NODE_SUBFOLDER' does not exist.\n"
  exit 2
fi

npm install --prefer-offline --no-audit --no-fund --loglevel error | grep -Ev "$NPM_INSTALL_OUTPUT_FILTER"

if [ $? -ne 0 ]; then
  printf "Error: Installing Node modules.\n"
  exit 2
fi

if [ "${VERBOSE:-}" -eq 1 ] 2>/dev/null; then
  printf "Building the application...\n"
fi

npm run build --loglevel silent | grep -v -E "Creating an optimized production build..." | sed '/The project was built assuming/,/https:\/\/cra\.link\/deployment/d'

if [ $? -ne 0 ]; then
  printf "Error: Building application.\n"
  exit 2
fi

if [ "${VERBOSE:-}" -eq 1 ] 2>/dev/null; then
  printf "Starting the application...\n"
fi

# Start the React app in the background and redirect output to a log file
BROWSER=none npm start > app.log 2>&1 &

# Capture the process ID of the npm start command
REACT_APP_PID=$!

# Wait for the "Compiled successfully!" message in the log file
tail -f app.log | grep -q -E "Compiled successfully!|Compiled with warnings."

# At this point, the React app is up and running in the background
if [ "${VERBOSE:-}" -eq 1 ] 2>/dev/null; then
  printf "React app is up and running!\n"
fi

# Execute all Cypress end-to-end tests in the build folder
printf "### Step 2: Running Cypress end-to-end tests $2...\n"

# Move back to the original directory
cd $current_dir

# Define the path to the e2e tests subfolder
NODE_E2E_TESTS_SUBFOLDER=node_$2

if [ "${VERBOSE:-}" -eq 1 ] 2>/dev/null; then
  printf "Preparing end-to-end tests Node subfolder: $NODE_E2E_TESTS_SUBFOLDER\n"
fi

# Check if the end-to-end tests node subfolder exists
if [ -d "$NODE_E2E_TESTS_SUBFOLDER" ]; then
  # Find and delete all files and folders except "node_modules", "build", and "package-lock.json"
  find "$NODE_E2E_TESTS_SUBFOLDER" -mindepth 1 ! -path "$NODE_E2E_TESTS_SUBFOLDER/node_modules*" ! -path "$NODE_E2E_TESTS_SUBFOLDER/build*" ! -name "package-lock.json" -exec rm -rf {} +
  
  if [ "${VERBOSE:-}" -eq 1 ] 2>/dev/null; then
    printf "Cleanup completed, keeping 'node_modules' and 'package-lock.json'.\n"
  fi
else
  if [ "${VERBOSE:-}" -eq 1 ] 2>/dev/null; then
    printf "Subfolder does not exist. Creating it...\n"
  fi

  mkdir -p $NODE_E2E_TESTS_SUBFOLDER
fi

cp -R $2/* $NODE_E2E_TESTS_SUBFOLDER

# Move to the subfolder with Cypress tests
cd "$NODE_E2E_TESTS_SUBFOLDER" 2>/dev/null

if [ $? -ne 0 ]; then
  printf "Error: e2e tests Node folder '$NODE_E2E_TESTS_SUBFOLDER' does not exist.\n"
  exit 2
fi

npm install cypress --save-dev --prefer-offline --no-audit --no-fund --loglevel error | grep -Ev "$NPM_INSTALL_OUTPUT_FILTER"

if [ "${VERBOSE:-}" -eq 1 ] 2>/dev/null; then
  printf "Running Cypress end-to-end tests...\n"
fi

BROWSERSLIST_IGNORE_OLD_DATA=1 npx cypress run --config video=false 2>/dev/null
cypress_run_result=$?

# Initialize an empty array to hold the PIDs
processes_to_kill=()

# Start the recursive search from the given parent PID
get_children $REACT_APP_PID

# Kill the main process
kill $REACT_APP_PID

# Kill all the subprocesses
for pid in "${processes_to_kill[@]}"
do
    kill $pid
done

if [ "${VERBOSE:-}" -eq 1 ] 2>/dev/null; then
  printf "React app is terminated!\n"
fi

if [ $cypress_run_result -ne 0 ]; then
  if [ "${VERBOSE:-}" -eq 1 ] 2>/dev/null; then
    printf "Error: Cypress end-to-end tests have failed.\n"
  fi
  exit 2
fi