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

# Execute all Golang unittests in the subfolder
echo "Running Golang unittests in $1..."
go test
