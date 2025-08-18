# Plain2Code CLI Reference

```text
usage: generate_cli.py [-h] [--verbose] [--base-folder] [--build-folder] [--config-name]
                       [--render-range | --render-from] [--unittests-script] [--conformance-tests-folder]
                       [--conformance-tests-script] [--api [API]] [--api-key] [--full-plain] [--dry-run] [--replay-with]
                       [--template-dir] [--copy-build] [--build-dest] [--copy-conformance-tests] [--conformance-tests-dest]
                       filename

Render plain code to target code.

positional arguments:
  filename              Path to the plain file to render. The directory containing this file has highest precedence for template loading, so you can place custom templates
                        here to override the defaults. See --template-dir for more details about template loading.

options:
  -h, --help            show this help message and exit
  --verbose, -v         Enable verbose output
  --base-folder
                        Base folder for the build files
  --build-folder (default: build)
                        Folder for build files
  --render-range
                        Specify a range of functional requirements to render (e.g. '1.1,2.3'). Use comma to separate start and end IDs. If only one ID is provided, only that
                        requirement is rendered. Range is inclusive of both start and end IDs.
  --render-from
                        Continue generation starting from this specific functional requirement (e.g. '2.1'). The requirement with this ID will be included in the output. The
                        ID must match one of the functional requirements in your plain file.
  --unittests-script
                        Shell script to run unit tests on generated code. It should receive the build folder path (containing generated source code) as first argument. The
                        build folder is the directory where plain2code generates all the source code files based on your plain specification. It's named 'build' by default
                        (unless you change it with --build-folder).
  --conformance-tests-folder (default: conformance_tests)
                        Folder for conformance test files
  --conformance-tests-script
                        Path to conformance tests shell script. The conformance tests shell script should accept the build folder path (containing generated source code) as
                        its first argument and the conformance tests folder path (containing test files) as its second argument. The build folder is the directory where
                        plain2code generates all the source code files based on your plain specification. The conformance tests folder contains the test files that verify the
                        generated code meets the requirements.
  --api [API]           Alternative base URL for the API. Default: `https://api.codeplain.ai`
  --api-key     API key used to access the API. If not provided, the CLAUDE_API_KEY environment variable is used.
  --full-plain          Show the complete specification that will be sent to the API for code generation. This displays your plain file content plus any additional
                        requirements that get automatically added. Useful for understanding what content is being processed.
  --dry-run             Preview of what Codeplain would do without actually making any changes.
  --replay-with
  --template-dir
                        Path to a custom template directory. Templates are searched in the following order: 1) directory containing the plain file, 2) this custom template
                        directory (if provided), 3) built-in standard_template_library directory
  --copy-build          If set, copy the build folder to `--build-dest` after every successful rendering.
  --build-dest (default: dist)
                        Target folder to copy build output to (used only if --copy-build is set).
  --copy-conformance-tests
                        If set, copy the conformance tests folder to `--conformance-tests-dest` after every successful rendering. Requires --conformance-tests-script.
  --conformance-tests-dest (default: dist_conformance_tests)
                        Target folder to copy conformance tests output to (used only if --copy-conformance-tests is set).

configuration:
  --config-name (default: config.yaml)
                        Path to the config file, defaults to config.yaml
```