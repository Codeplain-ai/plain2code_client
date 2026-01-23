#!/bin/bash

set -e

# Brand Colors (True Color / 24-bit)
YELLOW='\033[38;2;224;255;110m'    # #E0FF6E
GREEN='\033[38;2;121;252;150m'     # #79FC96
GREEN_LIGHT='\033[38;2;197;220;217m' # #C5DCD9
GREEN_DARK='\033[38;2;34;57;54m'   # #223936
BLUE='\033[38;2;10;31;212m'        # #0A1FD4
BLACK='\033[38;2;26;26;26m'        # #1A1A1A
WHITE='\033[38;2;255;255;255m'     # #FFFFFF
RED='\033[38;2;239;68;68m'         # #EF4444
GRAY='\033[38;2;128;128;128m'      # #808080
GRAY_LIGHT='\033[38;2;211;211;211m' # #D3D3D3
BOLD='\033[1m'
NC='\033[0m' # No Color / Reset

# Required Python version
REQUIRED_MAJOR=3
REQUIRED_MINOR=11

# Detect OS
detect_os() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    elif [[ -f /etc/debian_version ]]; then
        echo "debian"
    elif [[ -f /etc/redhat-release ]]; then
        echo "redhat"
    else
        echo "unknown"
    fi
}

echo -e "started ${YELLOW}${BOLD}*codeplain CLI${NC} installation..."

# Install Python based on OS
install_python() {
    local os=$(detect_os)
    
    case $os in
        macos)
            if command -v brew &> /dev/null; then
                echo -e "installing Python ${REQUIRED_MAJOR}.${REQUIRED_MINOR} via Homebrew..."
                brew install python@${REQUIRED_MAJOR}.${REQUIRED_MINOR}
            else
                echo -e "${RED}Error: Homebrew is not installed.${NC}"
                echo "please install Homebrew first: https://brew.sh"
                echo "or install Python manually from: https://www.python.org/downloads/"
                exit 1
            fi
            ;;
        debian)
            echo -e "installing Python ${REQUIRED_MAJOR}.${REQUIRED_MINOR} via apt..."
            sudo apt update
            sudo apt install -y python${REQUIRED_MAJOR}.${REQUIRED_MINOR} python${REQUIRED_MAJOR}.${REQUIRED_MINOR}-venv python3-pip
            ;;
        redhat)
            echo -e "installing Python ${REQUIRED_MAJOR}.${REQUIRED_MINOR} via dnf..."
            sudo dnf install -y python${REQUIRED_MAJOR}.${REQUIRED_MINOR}
            ;;
        *)
            echo -e "${RED}Error: Automatic installation not supported for your OS.${NC}"
            echo "please install Python ${REQUIRED_MAJOR}.${REQUIRED_MINOR} manually from:"
            echo "  https://www.python.org/downloads/"
            exit 1
            ;;
    esac
}

# Prompt user to install Python
prompt_install_python() {
    echo ""
    read -p "$(echo -e ${YELLOW}would you like to install Python ${REQUIRED_MAJOR}.${REQUIRED_MINOR}? \(Y/n\): ${NC})" response
    case "$response" in
        [yY][eE][sS]|[yY]|"")
            install_python
            echo ""
            echo -e "${GREEN}✓ python installed.${NC} please restart your terminal and run this script again."
            exit 0
            ;;
        *)
            echo -e "${YELLOW}installation cancelled.${NC}"
            exit 1
            ;;
    esac
}

# Check if python3 or python is installed
if command -v python3.11 &> /dev/null; then
    PYTHON_CMD="python3.11"
elif command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo -e "${RED}error: Python 3 is not installed.${NC}"
    prompt_install_python
fi

# Get Python version
PYTHON_VERSION=$($PYTHON_CMD -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)

# Check version
if [ "$PYTHON_MAJOR" -lt "$REQUIRED_MAJOR" ] || \
   ([ "$PYTHON_MAJOR" -eq "$REQUIRED_MAJOR" ] && [ "$PYTHON_MINOR" -lt "$REQUIRED_MINOR" ]); then
    echo -e "${RED}error: Python ${REQUIRED_MAJOR}.${REQUIRED_MINOR} or greater is required.${NC}"
    echo -e "found: python ${YELLOW}${PYTHON_VERSION}${NC}"
    prompt_install_python
fi

echo -e ""
echo -e "${GREEN}✓${NC} python ${BOLD}${PYTHON_VERSION}${NC} detected"
echo -e ""
# Use python -m pip for reliability
PIP_CMD="$PYTHON_CMD -m pip"

# Install or upgrade codeplain
if $PIP_CMD show codeplain &> /dev/null; then
    CURRENT_VERSION=$($PIP_CMD show codeplain | grep "^Version:" | cut -d' ' -f2)
    echo -e "${GRAY}codeplain ${CURRENT_VERSION} is already installed.${NC}"
    echo -e "upgrading to latest version..."
    echo -e ""
    $PIP_CMD install --upgrade codeplain &> /dev/null
    NEW_VERSION=$($PIP_CMD show codeplain | grep "^Version:" | cut -d' ' -f2)
    if [ "$CURRENT_VERSION" = "$NEW_VERSION" ]; then
        echo -e "${GREEN}✓${NC} codeplain is already up to date (${NEW_VERSION})"
    else
        echo -e "${GREEN}✓${NC} codeplain upgraded from ${CURRENT_VERSION} to ${NEW_VERSION}!"
    fi
else
    echo -e "installing codeplain...${NC}"
    echo -e ""
    $PIP_CMD install codeplain &> /dev/null
    echo -e "${GREEN}✓ codeplain installed successfully!${NC}"
fi

echo -e "${GREEN}✓${NC} the latest version of *codeplain CLI is now installed."
echo ""
echo -e "go to ${YELLOW}https://platform.codeplain.ai${NC} and sign up to get your API key."
echo ""
read -p "paste your API key here: " API_KEY
echo ""

if [ -z "$API_KEY" ]; then
    echo -e "${GRAY}no API key provided. you can set it later with:${NC}"
    echo -e "  export CODEPLAIN_API_KEY=\"your_api_key\""
else
    # Export for current session
    export CODEPLAIN_API_KEY="$API_KEY"
    
    # Detect user's default shell from $SHELL (works even when script runs in different shell)
    case "$SHELL" in
        */zsh)
            SHELL_RC="$HOME/.zprofile"
            ;;
        */bash)
            if [[ "$OSTYPE" == "darwin"* ]]; then
                # macOS uses .bash_profile for login shells
                SHELL_RC="$HOME/.bash_profile"
            else
                SHELL_RC="$HOME/.bashrc"
            fi
            ;;
        *)
            SHELL_RC="$HOME/.profile"
            ;;
    esac
    
    # Create the file if it doesn't exist
    touch "$SHELL_RC"
    
    # Add to shell config if not already present
    if ! grep -q "CODEPLAIN_API_KEY" "$SHELL_RC" 2>/dev/null; then
        echo "" >> "$SHELL_RC"
        echo "# codeplain API Key" >> "$SHELL_RC"
        echo "export CODEPLAIN_API_KEY=\"$API_KEY\"" >> "$SHELL_RC"
        echo -e "${GREEN}✓ API key saved to ${SHELL_RC}${NC}"
    else
        # Update existing key (different sed syntax for macOS vs Linux)
        if [[ "$OSTYPE" == "darwin"* ]]; then
            sed -i '' "s|export CODEPLAIN_API_KEY=.*|export CODEPLAIN_API_KEY=\"$API_KEY\"|" "$SHELL_RC"
        else
            sed -i "s|export CODEPLAIN_API_KEY=.*|export CODEPLAIN_API_KEY=\"$API_KEY\"|" "$SHELL_RC"
        fi
        echo -e "${GREEN}✓${NC} API key added to ${SHELL_RC}"
    fi
    
fi

# ASCII Art Welcome
echo ""
echo -e "${NC}"
echo -e "${GRAY}────────────────────────────────────────────${NC}"
echo -e ""
cat << 'EOF'
               _            _       _       
   ___ ___   __| | ___ _ __ | | __ _(_)_ __  
  / __/ _ \ / _` |/ _ \ '_ \| |/ _` | | '_ \ 
 | (_| (_) | (_| |  __/ |_) | | (_| | | | | |
  \___\___/ \__,_|\___| .__/|_|\__,_|_|_| |_|
                      |_|                    
EOF
echo ""
echo -e "  ${YELLOW}welcome to *codeplain!${NC}"
echo ""
echo -e "  spec-driven, production-ready code generation"
echo ""
echo ""
echo -e "${GRAY}────────────────────────────────────────────${NC}"
echo ""
echo -e "  thank you for using *codeplain!"
echo ""
echo -e "  run '${YELLOW}${BOLD}codeplain <path_to_plain_file>${NC}' to get started."
