# How to Start a New Plain Project from Scratch

This guide will walk you through creating your first Plain project from scratch.
It assumes you have already met all [prerequisites](../README.md#prerequisites), completed the [installation steps](../README.md/#installation-steps) and successfully rendered your first example. If you haven't done so yet, please refer to the [quick start section](../README.md#quick-start).
After following this guide, you'll be equipped to turn your ideas into working code with Plain.


We’ll use a simple array-sorting program as our example.
## 1. Create Your Project Directory

```bash
mkdir my-new-project
cd my-new-project
```

## 2. Define Your .plain File

Create a `.plain` file to specify your application's functionality, data structures, and acceptance tests. The following example shows a template for the array sorting problem. For more details, see [Plain language specifications](plain_language_specification.md).

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
    - When given input "5 2 8 1 9", The App should output "1 2 5 8 9"
    - When given input "-5 10 -2 0", The App should output "-5 -2 0 10"
    - When given input "1 2 3 4 5", The App should output "1 2 3 4 5"
    - When given input "42", The App should output "42"

```
**Notes:** 
- Use specific input/output examples to make tests concrete and verifiable.
- When including templates, use `--full-plain` flag to preview the complete specification including all template content before rendering. You can find predefined templates in [standard template library](../standard_template_library/).

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
- Specify the test scripts so that Plain knows how to run unit and conformance tests.
- Indicate where to copy the generated files and whether to display detailed output during code generation like shown in output control. 
- For full argument explanations, see the [plain2code CLI documentation](docs/plain2code_cli.md).


## 4. Add Test Scripts

Include the appropriate test scripts to your project:

```bash
mkdir test_scripts
cp /path/to/plain2code_client/test_scripts/run_unittests_python.sh ./test_scripts/
cp /path/to/plain2code_client/test_scripts/run_conformance_tests_python.sh ./test_scripts/
```
- You may need to modify these scripts based on your specific project requirements.

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
