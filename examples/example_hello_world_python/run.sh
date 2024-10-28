if [[ "$1" == "-v" || "$1" == "--verbose" ]]; then
  VERBOSE=1

  echo "Running Python hello world example in verbose mode."
fi


python ../../plain2code.py hello_world_python.plain ${VERBOSE:+-v}

# Check if the plain2code command failed
if [ $? -ne 0 ]; then
    echo "Error: The plain2code command failed."
    exit 1
fi

cd build

python ../harness_tests/hello_world_display/test_hello_world.py

# Check if the test harness has failed for the hello world example
if [ $? -ne 0 ]; then
    echo "Error: The test harness has failed for the hello world example."
    exit 1
fi

cd ..