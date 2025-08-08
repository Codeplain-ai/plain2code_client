# How to Start a New Plain Project from Scratch

## Prerequisites

- Python 3.8+ installed
- Git installed
- Access to plain2code tool
- Claude API key (for code generation)

## Installation

### 1. Install plain2code_client

```bash
# Clone the plain2code_client repository
git clone https://github.com/your-org/plain2code_client.git
cd plain2code_client

# Install dependencies
pip install -r requirements.txt

```

### 2. Environment Setup
Activate your target virtual environment and set up your Claude API key:

#### Export your API key (replace with your actual key)
export CLAUDE_API_KEY="your_api_key_here"

#### Verify the key is set
echo $CLAUDE_API_KEY
```
- Tip: Add this to your shell profile to avoid re-exporting every session.

**Troubleshooting:**
- If you get "module not found" or "API key not found", double-check you're in the correct venv and CLAUDE_API_KEY is set.
```

## 3. Create Your Project Directory

```bash
# Create your project folder
mkdir my-new-project && cd my-new-project
```

## 4. Define Your .plain File

Create a `.plain` file that describes your application. This is the core of your project.  
Add your specifications. For more details, have a look at Plain-language-specification.md

**Example: `my_app.plain`**
```plain
{% include "python-console-app-template.plain", main_executable_file_name: "my_app.py" %}


# "My Application Description" in plain

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
- `{% include %}` syntax allows you to use predefined templates

## 5. Configure config.yaml

Create a `config.yaml` file to configure your project behavior:

```yaml
# Test script configurations
unittests-script: ./test_scripts/run_unittests_python.sh
conformance-tests-script: ./test_scripts/run_conformance_tests_python.sh

# Output control
verbose: true
copy-build: true
copy-conformance-tests: true
```
### Explanation of config.yaml fields:
- unittests-script: Points to the script that runs unit tests for Python projects
- conformance-tests-script: Points to the script that runs conformance tests (acceptance tests) for Python projects
- verbose: When true, provides detailed output during the Plain2Code process
- copy-build: When true, copies the generated build artifacts to your project directory for easy access and version control
- copy-conformance-tests: When true, copies the generated conformance test files to your project directory, allowing you to review and modify the acceptance tests


## 6. Add Test Scripts

Copy the appropriate test scripts to your project:

```bash
# Create test_scripts directory
mkdir test_scripts

# Copy test scripts from plain2code_client
cp /path/to/plain2code_client/test_scripts/run_unittests_python.sh ./test_scripts/
cp /path/to/plain2code_client/test_scripts/run_conformance_tests_python.sh ./test_scripts/

```

## 7. Create .gitignore

Create a `.gitignore` file to exclude generated artifacts:

```gitignore
# AI-generated code/tests; reproducible, not source of truth:

build/
conformance_tests/
```

## 8. Run Your Project

```bash
# Generate code from your plain file
python ../plain2code_client/plain2code.py my_app.plain


```

## 9. Expected Project Layout

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

**Important Notes:**
- `build/` and `conformance_tests/` folders are generated automatically
- These folders are excluded from git via `.gitignore`
- `dist/` and `dist_conformance_tests/` are created if you set `copy-build: true` and `copy-conformance-tests: true` in your config.yaml
- Always review generated code before using in production
- The `.plain` file is your source of truth - keep it well-documented and version-controlled
