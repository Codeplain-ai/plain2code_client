if [[ "$1" == "-v" || "$1" == "--verbose" ]]; then
  VERBOSE=1

  echo "Running the hello world example for React in verbose mode."
fi

# Removing all the end-to-end tests before rendering the hello world example.
rm -rf e2e_tests
rm -rf node_e2e_tests

python ../../plain2code.py hello_world_react.plain --e2e-tests-script=../../test_scripts/run_e2e_tests_cypress.sh ${VERBOSE:+-v}

# Check if the plain2code command failed
if [ $? -ne 0 ]; then
    echo "Error: The plain2code command failed."
    exit 1
fi

../../test_scripts/run_e2e_tests_cypress.sh build harness_tests/hello_world_display ${VERBOSE:+-v}

# Check if the test harness has failed for the hello world example
if [ $? -ne 0 ]; then
    echo "Error: The test harness has failed for the hello world example."
    exit 1
fi
