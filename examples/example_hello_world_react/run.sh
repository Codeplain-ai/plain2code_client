# Store command line arguments
VERBOSE=0
API_ENDPOINT=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -v|--verbose)
            VERBOSE=1
            shift # Remove --verbose from processing
            ;;
        --api)
            API_ENDPOINT="$2"
            shift # Remove --api from processing
            shift # Remove the API endpoint value from processing
            ;;
        *)
            # Unknown option
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

if [ $VERBOSE -eq 1 ]; then
    echo "Running the hello world example for React in verbose mode."
fi

# Construct the command with optional parameters
CMD="python ../../plain2code.py hello_world_react.plain --conformance-tests-script=../../test_scripts/run_conformance_tests_cypress.sh"
if [ $VERBOSE -eq 1 ]; then
    CMD="$CMD -v"
fi
if [ ! -z "$API_ENDPOINT" ]; then
    CMD="$CMD --api $API_ENDPOINT"
fi

# Removing all the conformance tests before rendering the hello world example.
rm -rf conformance_tests
rm -rf node_conformance_tests

# Execute the command
$CMD

# Check if the plain2code command failed
if [ $? -ne 0 ]; then
    echo "Error: The plain2code command failed."
    exit 1
fi

../../test_scripts/run_conformance_tests_cypress.sh build harness_tests/hello_world_display ${VERBOSE:+-v}

# Check if the test harness has failed for the hello world example
if [ $? -ne 0 ]; then
    echo "Error: The test harness has failed for the hello world example."
    exit 1
fi
