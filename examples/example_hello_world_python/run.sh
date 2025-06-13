CONFIG_FILE="config.yaml"
VERBOSE=0

# Check if verbose is set in config.yaml and set VERBOSE accordingly
if grep -q "verbose: true" "$CONFIG_FILE" 2>/dev/null; then
    VERBOSE=1
fi

if [ $VERBOSE -eq 1 ]; then
    echo "Running the hello world example for Python in verbose mode."
fi

# Check if render-range and render-from exist in config.yaml
if ! (grep -q "render-range:" $CONFIG_FILE || grep -q "render-from:" $CONFIG_FILE); then
    echo "Removing conformance tests folder"
    rm -rf conformance_tests
fi

# Execute the command
python ../../plain2code.py hello_world_python.plain

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
