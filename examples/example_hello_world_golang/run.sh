# Store command line arguments
VERBOSE=0
CONFIG_FILE="config.yaml"

# Check if verbose is set in config.yaml and set VERBOSE accordingly
if grep -q "verbose: true" "$CONFIG_FILE" 2>/dev/null; then
    VERBOSE=1
fi

if [ $VERBOSE -eq 1 ]; then
    echo "Running Go lang hello world example in verbose mode."
fi

# Check if render-range and render-from exist in config.yaml
if ! (grep -q "render-range:" $CONFIG_FILE || grep -q "render-from:" $CONFIG_FILE); then
    echo "Removing conformance tests folder"
    rm -rf conformance_tests
fi

# Execute the command
python ../../plain2code.py hello_world_golang.plain

# Check if the plain2code command failed
if [ $? -ne 0 ]; then
    echo "Error: The plain2code command failed."
    exit 1
fi

cd build

# We need to compile the tests so that we can execute them in the current folder
# (https://stackoverflow.com/questions/23847003/golang-tests-and-working-directory/29541248#29541248)
go test -c ../harness_tests/hello_world_test.go

# Check if test compilation has failed for the hello world example
if [ $? -ne 0 ]; then
    echo "Error: The test harness has failed for the hello world example."
    exit 1
fi

./main.test