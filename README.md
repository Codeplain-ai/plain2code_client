# Codeplain plain2code renderer

Render Plain source to software code using the Codeplain API.

## Codeplain.ai - Code Generation as a Service

Codeplain is a platform that generates software code using large language models based on requirements you specify in Plain specification language.

Schematic overview of the Codeplain's code generation service

<img src="resources/codeplain_overview.png">

## Abstracting Away Code Generation Complexity with Plain

Plain is a novel specification language that helps abstracting away complexity of using large language models for code generation.

An example application in Plain

<img src="resources/plain_example.png" width="50%" height="50%">


See [Plain language specification](Plain-language-specification.md) for documentation how to use Plain language.


# Getting started

## Prerequisites

### System requirements

To run the plain2code client, you need Python 3.11 or a later version.
Review the [Platform specifics](#platform-specifics) section for setup details for your environment.

### Anthropic API Key

For now you need to bring your own Anthropic API key to use Codeplain API. If you don't have Anthropic API key, you can create a free developer account at [console.anthropic.com](https://console.anthropic.com/). To experiment with Codeplain you need to top up your Anthropic account with $5-10.

With Anthropic API Key ready, please contact Codeplain.ai support at support@codeplain.ai to have the hash of your Anthropic API key added to the list of authorized API keys.

To have the hash generated use the following command:

`python hash_key.py $CLAUDE_API_KEY`

### Setting Up Your API Key

```bash
# Export API key directly
export CLAUDE_API_KEY="your_actual_api_key_here"
```

## Installation Steps

1. Clone this repository
   ```
   git clone https://github.com/Codeplain-ai/plain2code.git
   cd plain2code
   ```
2. Set your Codeplain API key as an environment variable:
   ```
   export CLAUDE_API_KEY=your_api_key_here
   ```
3. Install required libraries
   ```
   pip install -r requirements.txt
   ```

4. Create a file, for example `hello.plain`, with your Plain specification.

5. Create a `config.yaml` file to configure your project behavior.
 
6. Execute:

   ```
   python plain2code.py hello.plain
   ```
7. The generated code will appear in the output folder (by default, `build/`).

# Additional Resources

- For more details on the Plain format, see the [Plain language specification](Plain-language-specification.md).
- Step-by-step instructions for creating your first Plain project. [Kickstart your plain project](Starting_a_plain_project_from_scratch.md)
- For complete CLI documentation and usage examples, see [plain2code CLI documentation](plain2code_cli_documentation.md)

# Examples

### "hello, world"

The "hello, world" examples reside in [examples](examples) folder and can be run with the following shell script:

`sh run.sh -v`


### Task manager

For example application how to implement task manager in Plain see [example-task-manager](https://github.com/Codeplain-ai/example-task-manager) repository.

### SaaS Connectors

For example application how to implement SaaS connectors in Plain see [example-saas-connectors](https://github.com/Codeplain-ai/example-saas-connectors) repository.


# Platform specifics

## Windows Environment Specifics

---

### 1. Prerequisites

- **Operating System:** Windows 10 or 11
- **Python:** Python 3.11 or later
- **WSL2 (Windows Subsystem for Linux):** Recommended if you encounter issues with shell scripts or need Unix tool compatibility
- **plain2code tool and API key:** See the [Getting started](#getting-started) section for instructions.

---

### 2. Troubleshooting Common Issues

#### Issue 1: CRLF Line Ending Problems

**Error:** `Error rendering plain code: [Errno 2] No such file or directory: '/path_to_test_scripts/test_scripts/run_unittests_python.sh'`

**Solution:**
```bash
# Check line endings
file /path_to_test_scripts/test_scripts/run_conformance_tests_python.sh

# Convert if needed
sudo apt-get install dos2unix
dos2unix /path_to_test_scripts/test_scripts/run_unittests_python.sh
dos2unix /path_to_test_scripts/test_scripts/run_conformance_tests_python.sh
```

#### Issue 2: Permission Issues

**Problem:** Scripts not executable

**Solution:**
```bash
# Make scripts executable
chmod +x test_scripts/run_unittests_python.sh
chmod +x test_scripts/run_conformance_tests_python.sh
```

#### Issue 3: Virtual Environment Issues

**Problem:** Module not found or API key not found

**Solution:**
```bash
source wsl_venv/bin/activate
which python  # Verify path
pip install -r requirements.txt --force-reinstall
```

### 3. Verification Steps

```bash
python --version
which python  # Should show wsl_venv
echo $CLAUDE_API_KEY
ls -la test_scripts/
file test_scripts/*.sh
```

## Mac Environment Specifics