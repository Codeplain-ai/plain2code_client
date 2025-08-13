# Windows Environment Setup for .plain Language Development

## Prerequisites

- Windows 10/11
- Python 3.8+ installed
- Git for Windows installed
- WSL2 (Windows Subsystem for Linux) - Recommended for better compatibility
- Access to plain2code tool
- Claude API key (for code generation)


## Installation Steps

### 1. Clone and Setup plain2code_client

```bash
git clone https://github.com/your-org/plain2code_client.git
cd plain2code_client

# Create and activate virtual environment
python -m venv wsl_venv
source wsl_venv/bin/activate  

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Configuration

#### Option A: Using .env file (Recommended)

```bash
echo "CLAUDE_API_KEY=your_actual_api_key_here" > .env
export $(cat .env | xargs)
```

#### Option B: Direct export

```bash
# Export API key directly
export CLAUDE_API_KEY="your_actual_api_key_here"
echo $CLAUDE_API_KEY  # Verify
```

## Troubleshooting Common Issues

### Issue 1: CRLF Line Ending Problems

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

### Issue 2: Permission Issues

**Problem:** Scripts not executable

**Solution:**
```bash
# Make scripts executable
chmod +x test_scripts/run_unittests_python.sh
chmod +x test_scripts/run_conformance_tests_python.sh
```

### Issue 3: Virtual Environment Issues

**Problem:** Module not found or API key not found

**Solution:**
```bash
source wsl_venv/bin/activate
which python  # Verify path
pip install -r requirements.txt --force-reinstall
```

## Verification Steps

```bash
python --version
which python  # Should show wsl_venv
echo $CLAUDE_API_KEY
ls -la test_scripts/
file test_scripts/*.sh
```

## Setup Summary

-  Python 3.8+ installed
-  Virtual environment created and activated (`wsl_venv`)
-  Dependencies installed (`pip install -r requirements.txt`)
-  API key set in environment
-  Git configured
-  Test scripts copied and have Unix line endings
-  Test scripts are executable
-  WSL2 properly configured (if using)
-  Paths use correct format for your environment

