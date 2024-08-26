# Codeplain plain2code renderer

Render software code from Plain source using the Codeplain API.

## Prerequisites

Please contact Codeplain.ai support at support@codeplain.ai to have the hash of your Anthropic Claude API key added to the list of authorized keys.

To have the hash generated use the following command:

`python hash_key.py $CLAUDE_API_KEY`

## Setup

1. Clone this repository
2. Set your Codeplain API key as an environment variable:
   ```
   export CLAUDE_API_KEY=your_api_key_here
   ```

## Usage
```
python plain2code.py [-h] [-v] [-V] [-b BUILD_FOLDER] [-B BASE_FOLDER] [-t TEST_SCRIPT] plain_source

Plain2Code: Convert plain text to software code.

positional arguments:
  plain_source          Path to The Plain Source file.

options:
  -h, --help            show this help message and exit
  -v, --verbose         Enable verbose output.
  -V, --version         show program's version number and exit
  -b BUILD_FOLDER, --build-folder BUILD_FOLDER
                        Specify the location of the build folder (default: build)
  -B BASE_FOLDER, --base-folder BASE_FOLDER
                        Specify the location of the base folder containing files to be copied to the build folder
  -t TEST_SCRIPT, --test-script TEST_SCRIPT
                        Specify a shell script to run unit tests. The script will receive the build folder as its parameter.
```

## Examples

### Hello, world

Python:

`python plain2code.py hello_world_python.plain -v`

Go lang:

`python plain2code.py hello_world_golang.plain -v`

### plain2code_client

`python plain2code.py plain2code_client.plain --unit-test-script=./run_unittests_python.sh --base-folder=base_folder --build-folder=plain2code_client -v`

## About Plain programming language

Plain is a novel programming language for a generative AI age. It uses large language models (LLM) to render software code from Plain source, freeing developers from the constraints of traditional compilers and fully separating functional specifications from implementation details.

The goal of the Plain programming language is to enhance productivity and innovation by enabling programmers to focus on creating more complex, intelligent applications with the support of AI.
