# CLI Reference

```text
usage: generate_cli.py [-h] [--verbose] [--base-folder BASE_FOLDER] [--build-folder BUILD_FOLDER]
                       [--config-name CONFIG_NAME] [--render-range RENDER_RANGE | --render-from RENDER_FROM]
                       [--unittests-script UNITTESTS_SCRIPT]
                       [--conformance-tests-folder CONFORMANCE_TESTS_FOLDER]
                       [--conformance-tests-script CONFORMANCE_TESTS_SCRIPT] [--api [API]] [--api-key API_KEY]
                       [--full-plain] [--dry-run] [--replay-with REPLAY_WITH] [--template-dir TEMPLATE_DIR]
                       [--copy-build] [--build-dest BUILD_DEST] [--copy-conformance-tests]
                       [--conformance-tests-dest CONFORMANCE_TESTS_DEST]
                       filename

Render plain code to target code.

positional arguments:
  filename              Path to the plain file to render. The directory containing this file has highest
                        precedence for template loading, so you can place custom templates here to override the
                        defaults. See --template-dir for more details about template loading.

options:
  -h, --help            show this help message and exit
  --verbose, -v         enable verbose output
  --base-folder BASE_FOLDER
                        base folder for the build files
  --build-folder BUILD_FOLDER
                        folder for build files
  --render-range RENDER_RANGE
                        which functional requirements should be generated
  --render-from RENDER_FROM
                        from which functional requirements generation should be continued
  --unittests-script UNITTESTS_SCRIPT
                        a script to run unit tests
  --conformance-tests-folder CONFORMANCE_TESTS_FOLDER
                        folder for conformance test files
  --conformance-tests-script CONFORMANCE_TESTS_SCRIPT
                        a script to run conformance tests
  --api [API]           force using the API (for internal use)
  --api-key API_KEY     API key used to access the API. If not provided, the CLAUDE_API_KEY environment
                        variable is used.
  --full-plain          emit full plain text to render
  --dry-run             preview what plain2code would do without actually making any changes
  --replay-with REPLAY_WITH
                        Replay the already executed render with provided render ID.
  --template-dir TEMPLATE_DIR
                        Path to a custom template directory. Templates are searched in the following order: 1)
                        directory containing the plain file, 2) this custom template directory (if provided),
                        3) built-in standard_template_library directory
  --copy-build          If set, copy the build folder to --build-dest after every successful rendering.
  --build-dest BUILD_DEST
                        Target folder to copy build output to (used only if --copy-build is set).
  --copy-conformance-tests
                        If set, copy the conformance tests folder to --conformance-tests-dest after every
                        successful rendering. Requires --conformance-tests-script.
  --conformance-tests-dest CONFORMANCE_TESTS_DEST
                        Target folder to copy conformance tests output to (used only if --copy-conformance-
                        tests is set).

configuration:
  --config-name CONFIG_NAME
                        path to the config file, defaults to config.yaml

```