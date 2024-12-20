# Codeplain plain2code renderer

Render Plain source to software code using the Codeplain API.

## About Codeplain.ai

Codeplain is a platform that helps you to generate software code using large language models based on requirements specified in Plain specification language.

Schematic overview of the Codeplain's code generation service

<img src="resources/codeplain_overview.png" width="75%" height="75%">

## About Plain specification language

Plain is a novel specification language that helps abstracting away complexity of using large language models for code generation.

An example application in Plain

<img src="resources/plain_example.png">


See [Plain language specification](Plain-language-specification.md) for documentation how to use Plain language.

## Examples

### "hello, world"

The "hello, world" examples reside in [examples](examples) folder and can be run with the following shell script:

`sh run.sh -v`


### Task manager

For example application how to implement task manager in Plain see [example-task-manager](https://github.com/Codeplain-ai/example-task-manager) repository.

### SaaS Connectors

For example application how to implement SaaS connectors in Plain see [example-saas-connectors](https://github.com/Codeplain-ai/example-saas-connectors) repository.

## Prerequisites

For now you need to bring your own LLM (Anthropic Claude) API key to use Codeplain API. Please contact Codeplain.ai support at support@codeplain.ai to have the hash of your Anthropic Claude API key added to the list of authorized API keys.

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
plain2code.py [-h] [--verbose] [--debug] [--base-folder BASE_FOLDER] [--build-folder BUILD_FOLDER]
    [--render-range RENDER_RANGE] [--unittests-script UNITTESTS_SCRIPT] [--e2e-tests-folder E2E_TESTS_FOLDER]
    [--e2e-tests-script E2E_TESTS_SCRIPT] [--api [API]] [--api-key API_KEY] filename

Render Plain source to software code.

positional arguments:
  filename              Path to The Plain Source file.

options:
  -h, --help            Show this help message and exit.
  --verbose, -v         Enable verbose output.
  --debug               Enable debug information.
  --base-folder BASE_FOLDER
                        Location of a folder whose content shoud be copied to the build folder
                        at the start of the rendering.
  --build-folder BUILD_FOLDER
                        Location of the build folder (default: build)
  --render-range RENDER_RANGE
                        Range of functional requirements to be renered
                        (e.g. "3,6" renders functional requirements 3, 4, 5, and 6).
  --unittests-script UNITTESTS_SCRIPT
                        Name of a shell script to run unit tests. The script will receive
                        the build folder as its parameter.
  --e2e-tests-folder E2E_TESTS_FOLDER
                        Location of the folder where generated end-to-end test files will be written.
  --e2e-tests-script E2E_TESTS_SCRIPT
                        Name of a shell script to run end-to-end tests. The script will receive
                        the build folder and the end-to-end tests subfolder as its parameters.
  --api [API]           Force using the API (for internal use).
  --api-key API_KEY     API key used to access the API. If not provided, the CLAUDE_API_KEY
                        environment variable is used.
```
