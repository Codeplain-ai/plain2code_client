echo "Running all example test harnesses..."

(
    printf "\nHELLO, WORLD (Python example)...\n\n"

    cd example_hello_world_python
    sh run.sh
    if [ $? -ne 0 ]; then
        echo "Hello World Python example failed."
        exit 1
    fi
    cd ..
)

(
    printf "\nHELLO, WORLD (Go lang example)...\n\n"

    cd example_hello_world_golang
    sh run.sh
    if [ $? -ne 0 ]; then
        echo "Hello World Golang example failed."
        exit 1
    fi
    cd ..
)

(
    printf "\nHELLO, WORLD (React example)...\n\n"

    cd example_hello_world_react
    sh run.sh
    if [ $? -ne 0 ]; then
        echo "Hello World React example failed."
        exit 1
    fi
    cd ..
)

echo "All example test harnesses completed successfully!"