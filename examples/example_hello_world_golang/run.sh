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