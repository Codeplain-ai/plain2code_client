# plain2code CLI Documentation

## Overview

The `plain2code.py` command-line tool renders plain code specifications to target code implementations.

## Usage

```bash
plain2code.py [OPTIONS] filename
```

## Command Line Arguments

**Default Configuration:**  
By default, configuration options are specified in the `config.yaml` file. Using a config file is recommended for clarity and reusability, as it keeps your settings organized and makes it easy to manage them across different runs.

### Positional Arguments

- **`filename`** - Path to the plain file to render. The directory containing this file has highest precedence for template loading, so you can place custom templates here to override the defaults. See `--template-dir` for more details about template loading.

### Options

#### General Options
- **`-h, --help`** - Show this help message and exit
- **`--verbose, -v`** - Enable verbose output
- **`--dry-run`** - Preview what plain2code would do without actually making any changes

#### Build Configuration
- **`--base-folder BASE_FOLDER`** - Base folder for the build files
- **`--build-folder BUILD_FOLDER`** - Folder for build files
- **`--config-name CONFIG_NAME`** - Path to the config file (defaults to `config.yaml`)

#### Rendering Control
- **`--render-range RENDER_RANGE`** - Which functional requirements should be generated
- **`--render-from RENDER_FROM`** - From which functional requirements generation should be continued
- **`--full-plain`** - Emit full plain text to render

#### Testing
- **`--unittests-script UNITTESTS_SCRIPT`** - A script to run unit tests
- **`--conformance-tests-folder CONFORMANCE_TESTS_FOLDER`** - Folder for conformance test files
- **`--conformance-tests-script CONFORMANCE_TESTS_SCRIPT`** - A script to run conformance tests

#### API Configuration
- **`--api [API]`** - Force using the API (for internal use)
- **`--api-key API_KEY`** - API key used to access the API. If not provided, the `CLAUDE_API_KEY` environment variable is used

#### Template Management
- **`--template-dir TEMPLATE_DIR`** - Path to a custom template directory. Templates are searched in the following order:
  1. Directory containing the plain file
  2. This custom template directory (if provided)
  3. Built-in `standard_template_library` directory

#### Build Output Management
- **`--copy-build`** - If set, copy the build folder to `--build-dest` after every successful functional requirement rendering
- **`--build-dest BUILD_DEST`** - Target folder to copy build output to (used only if `--copy-build` is set)
- **`--copy-conformance-tests`** - If set, copy the conformance tests folder to `--conformance-tests-dest` after every successful functional requirement rendering. Requires `--conformance-tests-script`
- **`--conformance-tests-dest CONFORMANCE_TESTS_DEST`** - Target folder to copy conformance tests output to (used only if `--copy-conformance-tests` is set)

#### Advanced Options
- **`--replay-with REPLAY_WITH`** - Replay the already executed render with provided render ID
