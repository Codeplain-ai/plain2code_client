# Windows Environment Specifics
This setup ensures you can run plain2code locally on Windows with an isolated Python environment and a valid API key

## 1. Prerequisites

- **Operating System:** Windows 10 or 11
- **Python:** Python 3.11 or later
- **WSL2 (Windows Subsystem for Linux):** Recommended if you encounter issues with shell scripts or need Unix tool compatibility
- **plain2code tool and API key:** See the [Getting started](#getting-started) section for instructions.

---

## 2. Setup Guide

1) Istall Python 3.11 or later for Windows
- Download from [python.org](python.org) 
- Check "Add Python to PATH" during installation
- Verify installation:
   ```
   python --version
   ```

2) Set Up Your API Key
    Set the environment variable:

    Command Prompt:
   ```
   setx CLAUDE_API_KEY "your_actual_api_key_here"
   ```
    PowerShell:
    ```
    $env:CLAUDE_API_KEY="your_api_key_here"
    ```
    Verify the key is set:
   ```
   echo %CLAUDE_API_KEY%
   ```

3) Create a Virtual Environment

     Create the virtual environment:
   ```
   python -m venv .venv
   ```
     Activate the virtual environment:
   ```
   .venv\Scripts\activate
   ```
     You should see `(.venv)` at the beginning of your command prompt

    **Quick note on virtual environments:** A virtual environment creates an isolated Python environment for your project, preventing conflicts between different projects' dependencies. It's like having a separate, clean Python installation just for this project. 
    
    Working with Virtual Environments:
    - **Activate:** `.venv\Scripts\activate`
    - **Deactivate:** `deactivate`
    - **Check if active:** Look for `(.venv)` at the start of your command prompt

4) Install Dependencies
    With the virtual environment activated, install the required packages:
   ```
   pip install -r requirements.txt
   ```

5) Verify Installation
   ```
   python --version
   where python
   echo %CLAUDE_API_KEY%
   ```

---

## 3. Troubleshooting Common Issues

### Issue 1: Virtual Environment Not Activating
**Problem:** `'activate' is not recognized as an internal or external command`

**Solution:**
1. Ensure you're in the correct directory
2. Check that the `.venv` folder exists
3. Try the full path: `.venv\Scripts\activate.bat`

### Issue 2: Module Not Found
**Problem:** `ModuleNotFoundError` when running plain2code

**Solution:**
1. Verify virtual environment is activated (should see `(.venv)`)
2. Reinstall dependencies:
   ```
   pip install -r requirements.txt --force-reinstall
   ```

### Issue 3: API Key Not Found
**Problem:** `CLAUDE_API_KEY` environment variable not set

**Solution:**
1. Set the environment variable:
   ```
   setx CLAUDE_API_KEY "your_actual_api_key_here"
   ```
2. Restart Command Prompt
3. Verify with: `echo %CLAUDE_API_KEY%`

### Issue 4: Shell Script Issues
**Problem:** Shell scripts (`.sh` files) won't run on Windows

**Solution:**
- Use WSL2 for shell script execution
- Or run the equivalent Python commands directly

### Issue 5: CRLF Line Ending Problems

**Error:** `Error rendering plain code: [Errno 2] No such file or directory: '/path_to_test_scripts/test_scripts/run_unittests_python.sh'`

**Solution:**
```bash
# Check line endings
file /path_to_test_scripts/test_scripts/run_conformance_tests_python.sh

# Convert if needed
sudo apt-get install dos2unix
dos2unix /path_to_test_scripts/test_scripts/run_unittests_python.sh
dos2unix /path_to_test_scripts/test_scripts/run_conformance_tests_python.sh
