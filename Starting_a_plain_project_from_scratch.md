# How to Start a New Plain Project from Scratch

This guide explains how to set up a new Plain project from scratch, write your `.plain` specification files, and generate your initial code outputs.

- For installation and environment setup see the main [README](README.md).

## 1. Create Your Project Directory

```bash
mkdir my-new-project
cd my-new-project
```

## 2. Define Your .plain File

Create a `.plain` file to specify your application's functionality, data structures, and acceptance tests. For more details, see [Plain language specifications](Plain-language-specification.md).

**Example: `my_app.plain`**
```plain
{% include "python-console-app-template.plain", main_executable_file_name: "my_app.py" %}

***Definitions:***
- The Array is an array of integers received as input.

***Functional Requirements:***
- The App should be extended to receive The Array
- Sort The Array.
- Display The Array.

    ***Acceptance Tests:***

    - The App should exit with status code 0 indicating successful execution
    - The App should complete execution in under 1 second
```

### Template System
- `{% include %}` syntax allows you to use predefined templates.

## 3. Configure config.yaml

Create a `config.yaml` file to configure your project behavior:

Example:
```yaml
# Test script configurations
unittests-script: ./test_scripts/run_unittests_python.sh
conformance-tests-script: ./test_scripts/run_conformance_tests_python.sh

# Output control
verbose: true
copy-build: true
copy-conformance-tests: true
```
- For full argument explanations, see the [plain2code CLI documentation](docs/plain2code_cli.md).


## 4. Add Test Scripts

Copy the appropriate test scripts to your project:

```bash
mkdir test_scripts
cp /path/to/plain2code_client/test_scripts/run_unittests_python.sh ./test_scripts/
cp /path/to/plain2code_client/test_scripts/run_conformance_tests_python.sh ./test_scripts/
```

## 5. Create .gitignore

Exclude generated artifacts from version control:

```gitignore
# AI-generated code/tests
build/
conformance_tests/
```

## 6. Generate & Run Your Project

```bash
python ../plain2code_client/plain2code.py my_app.plain
```
- Generated code will appear in build/ and conformance_tests/.

## 7. Expected Project Layout

```
my-new-project/
├── my_app.plain                   
├── config.yaml                     
├── test_scripts/                  
├── README.md                     
├── .gitignore                      
├── build/                          # Generated
├── conformance_tests/              # Generated
├── dist/                           # Build output (if copy-build: true)
└── dist_conformance_tests/         # Test output (if copy-conformance-tests: true)
```

## 8. Notes
- `build/` and `conformance_tests/` folders are generated automatically
- These folders are excluded from git via `.gitignore`
- `dist/` and `dist_conformance_tests/` are created if you set `copy-build: true` and `copy-conformance-tests: true` in your config.yaml
- Always review generated code before using in production
- The `.plain` file is your source of truth - keep it well-documented and version-controlled
