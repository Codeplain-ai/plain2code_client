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

echo "Running all example test harnesses..."

(
    printf "\nHELLO, WORLD (Python example)...\n\n"

    cd example_hello_world_python
    sh run.sh ${VERBOSE:+-v} ${RENDER_RANGE:+"--render-range=$RENDER_RANGE"} ${RENDER_FROM:+"--render-from=$RENDER_FROM"} ${API_ENDPOINT:+"--api $API_ENDPOINT"}
    if [ $? -ne 0 ]; then
        echo "Hello World Python example failed."
        exit 1
    fi
    cd ..
)

(
    printf "\nHELLO, WORLD (Go lang example)...\n\n"

    cd example_hello_world_golang
    sh run.sh ${VERBOSE:+-v} ${RENDER_RANGE:+"--render-range=$RENDER_RANGE"} ${RENDER_FROM:+"--render-from=$RENDER_FROM"} ${API_ENDPOINT:+"--api $API_ENDPOINT"}
    if [ $? -ne 0 ]; then
        echo "Hello World Golang example failed."
        exit 1
    fi
    cd ..
)

(
    printf "\nHELLO, WORLD (React example)...\n\n"

    cd example_hello_world_react
    sh run.sh ${VERBOSE:+-v} ${RENDER_RANGE:+"--render-range=$RENDER_RANGE"} ${RENDER_FROM:+"--render-from=$RENDER_FROM"} ${API_ENDPOINT:+"--api $API_ENDPOINT"}
    if [ $? -ne 0 ]; then
        echo "Hello World React example failed."
        exit 1
    fi
    cd ..
)

echo "All example test harnesses completed successfully!"