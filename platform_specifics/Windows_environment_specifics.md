# Windows Environment Specifics

This is a guide for users running Codeplain on the Windows operating system. Codeplain supports running on Windows via WSL, so please make sure you have WSL installed before proceeding.

## 1. Prerequisites

- **Operating System:** Windows 10 or 11
- **WSL2 (Windows Subsystem for Linux)** 

## 2. Setup Guide Specifics

### 1. Setting Up Your API Key

   Command Prompt:
   ```
   setx CLAUDE_API_KEY "your_actual_api_key_here"
   ```
   PowerShell (applies to your current session):

      $env:CLAUDE_API_KEY="your_api_key_here"
    
### 2. Activation of a Virtual Environment

   ```
   .venv\Scripts\activate
   ```
   You should see `(.venv)` at the beginning of your command prompt


### 3. CRLF Line Ending Problems
Convert line endings if you run into script execution errors:

```bash
sudo apt-get install dos2unix
dos2unix /path_to_test_scripts/test_scripts/run_unittests_python.sh
dos2unix /path_to_test_scripts/test_scripts/run_conformance_tests_python.sh
```
