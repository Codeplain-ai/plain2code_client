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
        --render-range)
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
    echo "Running Go lang hello world example in verbose mode."
fi

# Construct the command with optional parameters
CMD="python ../../plain2code.py hello_world_golang.plain --unittests-script=../../test_scripts/run_unittests_golang.sh --conformance-tests-script=../../test_scripts/run_conformance_tests_golang.sh ${VERBOSE:+-v} ${RENDER_RANGE:+"--render-range=$RENDER_RANGE"} ${RENDER_FROM:+"--render-from=$RENDER_FROM"} ${API_ENDPOINT:+"--api $API_ENDPOINT"}"

# Removing all the conformance tests before rendering the hello world example.
rm -rf conformance_tests

# Execute the command
$CMD

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