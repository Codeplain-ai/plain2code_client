if [[ "$1" == "-v" || "$1" == "--verbose" ]]; then
  VERBOSE=1

  printf "Running plain2code test harness in verbose mode.\n\n"
fi

(
	cd example_hello_world_python

	sh run.sh ${VERBOSE:+-v}

	# Check if the example_hello_world/run.sh command failed
	if [ $? -ne 0 ]; then
    	echo "Error: The example_hello_world/run.sh command failed."
    	exit 1
	fi
)

(
	cd example_hello_world_golang

	sh run.sh ${VERBOSE:+-v}

	# Check if the example_hello_world/run.sh command failed
	if [ $? -ne 0 ]; then
    	echo "Error: The example_hello_world/run.sh command failed."
    	exit 1
	fi
)

(
	cd example_hello_world_react

	sh run.sh ${VERBOSE:+-v}

	# Check if the example_hello_world/run.sh command failed
	if [ $? -ne 0 ]; then
    	echo "Error: The example_hello_world/run.sh command failed."
    	exit 1
	fi
)