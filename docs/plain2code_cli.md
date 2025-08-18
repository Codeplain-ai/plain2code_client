# Plain2Code CLI Reference

```text
usage: generate_cli.py [-h] [--verbose] [--base-folder BASE_FOLDER] [--build-folder BUILD_FOLDER] [--config-name CONFIG_NAME]
                       [--render-range RENDER_RANGE | --render-from RENDER_FROM] [--unittests-script UNITTESTS_SCRIPT]
                       [--conformance-tests-folder CONFORMANCE_TESTS_FOLDER] [--conformance-tests-script CONFORMANCE_TESTS_SCRIPT]
                       [--api [API]] [--api-key API_KEY] [--full-plain] [--dry-run] [--replay-with REPLAY_WITH]
                       [--template-dir TEMPLATE_DIR] [--copy-build] [--build-dest BUILD_DEST] [--copy-conformance-tests]
                       [--conformance-tests-dest CONFORMANCE_TESTS_DEST]
                       filename

Render plain code to target code.

positional arguments:
  filename              Path to the plain file to render. The directory containing this file has highest precedence for template
                        loading, so you can place custom templates here to override the defaults. See --template-dir for more
                        details about template loading.

options:
  -h, --help            show this help message and exit
  --verbose, -v         Enable verbose output
  --base-folder BASE_FOLDER
                        Base folder for the build files
  --build-folder BUILD_FOLDER
                        Folder for build files
  --render-range RENDER_RANGE
                        Specify a range of functional requirements to render (e.g. '1.1,2.3'). Use comma to separate start and end
                        IDs. If only one ID is provided, only that requirement is rendered. Range is inclusive of both start and
                        end IDs.
  --render-from RENDER_FROM
                        Continue generation starting from this specific functional requirement (e.g. '2.1'). The requirement with
                        this ID will be included in the output. The ID must match one of the functional requirements in your plain
                        file.
  --unittests-script UNITTESTS_SCRIPT
                        Shell script to run unit tests on generated code. Receives the build folder path as its first argument
                        (default: 'build').
  --conformance-tests-folder CONFORMANCE_TESTS_FOLDER
                        Folder for conformance test files
  --conformance-tests-script CONFORMANCE_TESTS_SCRIPT
                        Path to conformance tests shell script. The conformance tests shell script should accept the build folder
                        path (containing generated source code) as its first argument and the conformance tests folder path
                        (containing test files) as its second argument.
  --api [API]           Alternative base URL for the API. Default: `https://api.codeplain.ai`
  --api-key API_KEY     API key used to access the API. If not provided, the CLAUDE_API_KEY environment variable is used.
  --full-plain          Display the complete plain specification before code generation. This shows your plain file with any
                        included template content expanded. Useful for understanding what content is being processed.
  --dry-run             Preview of what Codeplain would do without actually making any changes.
  --replay-with REPLAY_WITH
  --template-dir TEMPLATE_DIR
                        Path to a custom template directory. Templates are searched in the following order: 1) directory containing
                        the plain file, 2) this custom template directory (if provided), 3) built-in standard_template_library
                        directory
  --copy-build          If set, copy the build folder to `--build-dest` after every successful rendering.
  --build-dest BUILD_DEST
                        Target folder to copy build output to (used only if --copy-build is set).
  --copy-conformance-tests
                        If set, copy the conformance tests folder to `--conformance-tests-dest` after every successful rendering.
                        Requires --conformance-tests-script.
  --conformance-tests-dest CONFORMANCE_TESTS_DEST
                        Target folder to copy conformance tests output to (used only if --copy-conformance-tests is set).

configuration:
  --config-name CONFIG_NAME
                        Path to the config file, defaults to config.yaml

```