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
        --render-range )
            shift
            RENDER_RANGE=$1
            shift
            ;;
        --render-from)
            shift
            RENDER_FROM=$1
            shift
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
    echo "Running Python hello world example in verbose mode."
fi

# Construct the command with optional parameters
CMD="python ../../plain2code.py hello_world_python.plain --unittests-script=../../test_scripts/run_unittests_python.sh --conformance-tests-script=../../test_scripts/run_conformance_tests_python.sh ${VERBOSE:+-v} ${RENDER_RANGE:+"--render-range=$RENDER_RANGE"} ${RENDER_FROM:+"--render-from=$RENDER_FROM"} ${API_ENDPOINT:+"--api $API_ENDPOINT"}"

echo "Removing conformance tests folder"
rm -rf conformance_tests

# Execute the command
$CMD

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
