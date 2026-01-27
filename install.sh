#!/bin/bash

set -euo pipefail

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

clear
echo -e "started ${YELLOW}${BOLD}*codeplain CLI${NC} installation..."

# Install uv if not present
install_uv() {
    echo -e "installing uv package manager..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    # Add uv to PATH for this session
    export PATH="$HOME/.local/bin:$PATH"
}

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo -e "${GRAY}uv is not installed.${NC}"
    install_uv
    echo -e "${GREEN}✓${NC} uv installed successfully"
    echo -e ""
fi

echo -e "${GREEN}✓${NC} uv detected"
echo -e ""

# Install or upgrade codeplain using uv tool
if uv tool list 2>/dev/null | grep -q "^codeplain"; then
    CURRENT_VERSION=$(uv tool list 2>/dev/null | grep "^codeplain" | sed 's/codeplain v//')
    echo -e "${GRAY}codeplain ${CURRENT_VERSION} is already installed.${NC}"
    echo -e "upgrading to latest version..."
    echo -e ""
    uv tool upgrade codeplain &> /dev/null
    NEW_VERSION=$(uv tool list 2>/dev/null | grep "^codeplain" | sed 's/codeplain v//')
    if [ "$CURRENT_VERSION" = "$NEW_VERSION" ]; then
        echo -e "${GREEN}✓${NC} codeplain is already up to date (${NEW_VERSION})"
    else
        echo -e "${GREEN}✓${NC} codeplain upgraded from ${CURRENT_VERSION} to ${NEW_VERSION}!"
    fi
else
    echo -e "installing codeplain...${NC}"
    echo -e ""
    uv tool install codeplain
    clear
    echo -e "${GREEN}✓ codeplain installed successfully!${NC}"
fi

# Check if API key already exists
SKIP_API_KEY_SETUP=false
if [ -n "${CODEPLAIN_API_KEY:-}" ]; then
    echo -e "  you already have an API key configured."
    echo ""
    echo -e "  would you like to log in and get a new one?"
    echo ""
    read -p "  [y/N]: " GET_NEW_KEY </dev/tty
    echo ""

    if [[ ! "$GET_NEW_KEY" =~ ^[Yy]$ ]]; then
        echo -e "${GREEN}✓${NC} using existing API key."
        SKIP_API_KEY_SETUP=true
    fi
fi

if [ "$SKIP_API_KEY_SETUP" = false ]; then
    echo -e "go to ${YELLOW}https://platform.codeplain.ai${NC} and sign up to get your API key."
    echo ""
    read -r -p "paste your API key here: " API_KEY < /dev/tty
    echo ""
fi

if [ "$SKIP_API_KEY_SETUP" = true ]; then
    : # API key already set, nothing to do
elif [ -z "$API_KEY" ]; then
    echo -e "${GRAY}no API key provided. you can set it later with:${NC}"
    echo -e "  export CODEPLAIN_API_KEY=\"your_api_key\""
else
    # Export for current session
    export CODEPLAIN_API_KEY="$API_KEY"

    # Detect user's default shell from $SHELL (works even when script runs in different shell)
    case "$SHELL" in
        */zsh)
            SHELL_RC="$HOME/.zshrc"
            ;;
        */bash)
            SHELL_RC="$HOME/.bashrc"
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
    fi
fi

# ASCII Art Welcome
clear
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
echo -e "${GREEN}✓${NC} Sign in successful."
echo ""
echo -e "  ${YELLOW}welcome to *codeplain!${NC}"
echo ""
echo -e "  spec-driven, production-ready code generation"
echo ""
echo ""
echo -e "${GRAY}────────────────────────────────────────────${NC}"
echo ""
echo -e "  would you like to get a quick intro to ***plain specification language?"
echo ""
read -p "  [Y/n]: " WALKTHROUGH_CHOICE </dev/tty
echo ""

# Default to yes if empty, check for explicit no
if [[ ! "$WALKTHROUGH_CHOICE" =~ ^[Nn]$ ]]; then

# Onboarding Step 1: Introduction to Plain
clear
echo ""
echo -e "${GRAY}────────────────────────────────────────────${NC}"
echo -e "  ${YELLOW}${BOLD}quick intro to ***plain specification language{NC} - Step 1 of 5"
echo -e "${GRAY}────────────────────────────────────────────${NC}"
echo ""
echo -e "  ***plain is a language of spec-driven development that allows developers to express intent on any level of detail."
echo ""
echo -e "  write specs in ${YELLOW}plain English${NC}, in markdown with additional syntax"
echo ""
echo -e "  render production-ready code with *codeplain."
echo ""
echo -e "  A ***plain file has these key sections:"
echo ""
echo -e "${GRAY}  ┌────────────────────────────────────────────────────────┐${NC}"
echo -e "${GRAY}  │${NC}                                                        ${GRAY}│${NC}"
echo -e "${GRAY}  │${NC}  ${YELLOW}***definitions***${NC}      - key concepts in your app     ${GRAY}│${NC}"
echo -e "${GRAY}  │${NC}  ${YELLOW}***technical specs***${NC}  - implementation details       ${GRAY}│${NC}"
echo -e "${GRAY}  │${NC}  ${YELLOW}***test specs***${NC}       - testing requirements         ${GRAY}│${NC}"
echo -e "${GRAY}  │${NC}  ${YELLOW}***functional specs***${NC} - what the app should do       ${GRAY}│${NC}"
echo -e "${GRAY}  │${NC}                                                        ${GRAY}│${NC}"
echo -e "${GRAY}  └────────────────────────────────────────────────────────┘${NC}"
echo ""
echo -e "  Let's see each section in a \"hello, world\" example."
echo ""
read -p "  press [Enter] to continue..." </dev/tty

# Onboarding Step 2: Functional Specification
clear
echo ""
echo -e "${GRAY}────────────────────────────────────────────${NC}"
echo -e "  ${YELLOW}${BOLD}Plain Language 101${NC} - Step 2 of 5"
echo -e "${GRAY}────────────────────────────────────────────${NC}"
echo ""
echo -e "  ${WHITE}${BOLD}FUNCTIONAL SPECS${NC} - what should the app do?"
echo ""
echo -e "  This is where you describe ${GREEN}what your app should do${NC},"
echo -e "  written in plain English. No code, just requirements."
echo ""
echo -e "${GRAY}  ┌────────────────────────────────────────────────────────┐${NC}"
echo -e "${GRAY}  │${NC}                                                        ${GRAY}│${NC}"
echo -e "${GRAY}  │${NC}  ${GRAY}***definitions***${NC}                                    ${GRAY}│${NC}"
echo -e "${GRAY}  │${NC}                                                        ${GRAY}│${NC}"
echo -e "${GRAY}  │${NC}  ${GRAY}- :App: is a console application.${NC}                    ${GRAY}│${NC}"
echo -e "${GRAY}  │${NC}                                                        ${GRAY}│${NC}"
echo -e "${GRAY}  │${NC}  ${GRAY}***technical specs***${NC}                                ${GRAY}│${NC}"
echo -e "${GRAY}  │${NC}                                                        ${GRAY}│${NC}"
echo -e "${GRAY}  │${NC}  ${GRAY}- :Implementation: should be in Python.${NC}              ${GRAY}│${NC}"
echo -e "${GRAY}  │${NC}  ${GRAY}- :UnitTests: should use Unittest framework.${NC}         ${GRAY}│${NC}"
echo -e "${GRAY}  │${NC}                                                        ${GRAY}│${NC}"
echo -e "${GRAY}  │${NC}  ${GRAY}***test specs***${NC}                                     ${GRAY}│${NC}"
echo -e "${GRAY}  │${NC}                                                        ${GRAY}│${NC}"
echo -e "${GRAY}  │${NC}  ${GRAY}- :ConformanceTests: should use Unittest.${NC}            ${GRAY}│${NC}"
echo -e "${GRAY}  │${NC}                                                        ${GRAY}│${NC}"
echo -e "${GRAY}  │${NC}  ${YELLOW}${BOLD}***functional specs***${NC}                               ${GRAY}│${NC}"
echo -e "${GRAY}  │${NC}                                                        ${GRAY}│${NC}"
echo -e "${GRAY}  │${NC}  ${GREEN}${BOLD}- :App: should display \"hello, world\".${NC}               ${GRAY}│${NC}"
echo -e "${GRAY}  │${NC}                                                        ${GRAY}│${NC}"
echo -e "${GRAY}  └────────────────────────────────────────────────────────┘${NC}"
echo ""
echo -e "  ${GREEN}▲${NC} The ${YELLOW}functional spec${NC} describes ${GREEN}what${NC} the app does."
echo -e "    Here, it simply displays \"hello, world\"."
echo ""
read -p "  press [Enter] to continue..." </dev/tty

# Onboarding Step 3: Definitions
clear
echo ""
echo -e "${GRAY}────────────────────────────────────────────${NC}"
echo -e "  ${YELLOW}${BOLD}Plain Language 101${NC} - Step 3 of 5"
echo -e "${GRAY}────────────────────────────────────────────${NC}"
echo ""
echo -e "  ${WHITE}${BOLD}DEFINITIONS${NC} - identify key concepts"
echo ""
echo -e "  Define ${GREEN}reusable concepts${NC} with the ${YELLOW}:ConceptName:${NC} syntax."
echo -e "  These become building blocks you can reference anywhere."
echo ""
echo -e "${GRAY}  ┌────────────────────────────────────────────────────────┐${NC}"
echo -e "${GRAY}  │${NC}                                                        ${GRAY}│${NC}"
echo -e "${GRAY}  │${NC}  ${YELLOW}${BOLD}***definitions***${NC}                                    ${GRAY}│${NC}"
echo -e "${GRAY}  │${NC}                                                        ${GRAY}│${NC}"
echo -e "${GRAY}  │${NC}  ${GREEN}${BOLD}- :App: is a console application.${NC}                    ${GRAY}│${NC}"
echo -e "${GRAY}  │${NC}                                                        ${GRAY}│${NC}"
echo -e "${GRAY}  │${NC}  ${GRAY}***technical specs***${NC}                                ${GRAY}│${NC}"
echo -e "${GRAY}  │${NC}                                                        ${GRAY}│${NC}"
echo -e "${GRAY}  │${NC}  ${GRAY}- :Implementation: should be in Python.${NC}              ${GRAY}│${NC}"
echo -e "${GRAY}  │${NC}  ${GRAY}- :UnitTests: should use Unittest framework.${NC}         ${GRAY}│${NC}"
echo -e "${GRAY}  │${NC}                                                        ${GRAY}│${NC}"
echo -e "${GRAY}  │${NC}  ${GRAY}***test specs***${NC}                                     ${GRAY}│${NC}"
echo -e "${GRAY}  │${NC}                                                        ${GRAY}│${NC}"
echo -e "${GRAY}  │${NC}  ${GRAY}- :ConformanceTests: should use Unittest.${NC}            ${GRAY}│${NC}"
echo -e "${GRAY}  │${NC}                                                        ${GRAY}│${NC}"
echo -e "${GRAY}  │${NC}  ${GRAY}***functional specs***${NC}                               ${GRAY}│${NC}"
echo -e "${GRAY}  │${NC}                                                        ${GRAY}│${NC}"
echo -e "${GRAY}  │${NC}  ${GRAY}- :App: should display \"hello, world\".${NC}               ${GRAY}│${NC}"
echo -e "${GRAY}  │${NC}                                                        ${GRAY}│${NC}"
echo -e "${GRAY}  └────────────────────────────────────────────────────────┘${NC}"
echo ""
echo -e "  ${GREEN}▲${NC} The ${YELLOW}:App:${NC} concept is defined once and used throughout."
echo -e "    Concepts help keep your specs consistent and clear."
echo ""
read -p "  press [Enter] to continue..." </dev/tty

# Onboarding Step 4: Technical & Test Specs
clear
echo ""
echo -e "${GRAY}────────────────────────────────────────────${NC}"
echo -e "  ${YELLOW}${BOLD}Plain Language 101${NC} - Step 4 of 5"
echo -e "${GRAY}────────────────────────────────────────────${NC}"
echo ""
echo -e "  ${WHITE}${BOLD}TECHNICAL & TEST SPECS${NC} - how to implement and test"
echo ""
echo -e "  Specify ${GREEN}implementation details${NC} and ${GREEN}testing requirements${NC}."
echo -e "  This guides how the code should be generated and verified."
echo ""
echo -e "${GRAY}  ┌────────────────────────────────────────────────────────┐${NC}"
echo -e "${GRAY}  │${NC}                                                        ${GRAY}│${NC}"
echo -e "${GRAY}  │${NC}  ${GRAY}***definitions***${NC}                                    ${GRAY}│${NC}"
echo -e "${GRAY}  │${NC}                                                        ${GRAY}│${NC}"
echo -e "${GRAY}  │${NC}  ${GRAY}- :App: is a console application.${NC}                    ${GRAY}│${NC}"
echo -e "${GRAY}  │${NC}                                                        ${GRAY}│${NC}"
echo -e "${GRAY}  │${NC}  ${YELLOW}${BOLD}***technical specs***${NC}                                ${GRAY}│${NC}"
echo -e "${GRAY}  │${NC}                                                        ${GRAY}│${NC}"
echo -e "${GRAY}  │${NC}  ${GREEN}${BOLD}- :Implementation: should be in Python.${NC}              ${GRAY}│${NC}"
echo -e "${GRAY}  │${NC}  ${GREEN}${BOLD}- :UnitTests: should use Unittest framework.${NC}         ${GRAY}│${NC}"
echo -e "${GRAY}  │${NC}                                                        ${GRAY}│${NC}"
echo -e "${GRAY}  │${NC}  ${YELLOW}${BOLD}***test specs***${NC}                                     ${GRAY}│${NC}"
echo -e "${GRAY}  │${NC}                                                        ${GRAY}│${NC}"
echo -e "${GRAY}  │${NC}  ${GREEN}${BOLD}- :ConformanceTests: should use Unittest.${NC}            ${GRAY}│${NC}"
echo -e "${GRAY}  │${NC}                                                        ${GRAY}│${NC}"
echo -e "${GRAY}  │${NC}  ${GRAY}***functional specs***${NC}                               ${GRAY}│${NC}"
echo -e "${GRAY}  │${NC}                                                        ${GRAY}│${NC}"
echo -e "${GRAY}  │${NC}  ${GRAY}- :App: should display \"hello, world\".${NC}               ${GRAY}│${NC}"
echo -e "${GRAY}  │${NC}                                                        ${GRAY}│${NC}"
echo -e "${GRAY}  └────────────────────────────────────────────────────────┘${NC}"
echo ""
echo -e "  ${GREEN}▲${NC} ${YELLOW}Technical specs${NC} define the language and frameworks."
echo -e "    ${YELLOW}Test specs${NC} ensure the generated code is verified."
echo ""
read -p "  press [Enter] to continue..." </dev/tty

# Onboarding Step 5: Rendering Code
clear
echo ""
echo -e "${GRAY}────────────────────────────────────────────${NC}"
echo -e "  ${YELLOW}${BOLD}Plain Language 101${NC} - Step 5 of 5"
echo -e "${GRAY}────────────────────────────────────────────${NC}"
echo ""
echo -e "  ${WHITE}${BOLD}RENDERING CODE${NC} - generate your app"
echo ""
echo -e "  Once you have a Plain file, generate code with:"
echo ""
echo -e "    ${YELLOW}${BOLD}codeplain hello_world.plain${NC}"
echo ""
echo -e "  *codeplain will:"
echo ""
echo -e "    ${GREEN}1.${NC} Read your specification"
echo -e "    ${GREEN}2.${NC} Generate implementation code"
echo -e "    ${GREEN}3.${NC} Create and run tests to verify correctness"
echo -e "    ${GREEN}4.${NC} Output production-ready code"
echo ""
echo -e "  The generated code is guaranteed to match your specs"
echo -e "  and pass all defined tests."
echo ""
read -p "  press [Enter] to finish..." </dev/tty

fi  # End of walkthrough conditional

# Download examples step
clear
echo ""
echo -e "${GRAY}────────────────────────────────────────────${NC}"
echo -e "  ${YELLOW}${BOLD}Example Projects${NC}"
echo -e "${GRAY}────────────────────────────────────────────${NC}"
echo ""
echo -e "  we've prepared some example Plain projects for you"
echo -e "  to explore and experiment with."
echo ""
echo -e "  would you like to download them?"
echo ""
read -p "  [Y/n]: " DOWNLOAD_EXAMPLES </dev/tty
echo ""

if [[ ! "$DOWNLOAD_EXAMPLES" =~ ^[Nn]$ ]]; then
    # Show current directory and ask for extraction path
    CURRENT_DIR=$(pwd)
    echo -e "  current folder: ${YELLOW}${CURRENT_DIR}${NC}"
    echo ""
    echo -e "  extract examples here, or enter a different path:"
    echo ""
    read -p "  [Enter for current, or type path]: " EXTRACT_PATH </dev/tty
    echo ""

    # Use current directory if empty
    if [ -z "$EXTRACT_PATH" ]; then
        EXTRACT_PATH="$CURRENT_DIR"
    fi

    # Expand ~ to home directory
    EXTRACT_PATH="${EXTRACT_PATH/#\~/$HOME}"

    # Check if directory exists, create if not
    if [ ! -d "$EXTRACT_PATH" ]; then
        echo -e "  ${GRAY}creating directory...${NC}"
        mkdir -p "$EXTRACT_PATH" 2>/dev/null
        if [ $? -ne 0 ]; then
            echo -e "  ${RED}✗${NC} failed to create directory: ${EXTRACT_PATH}"
            echo -e "  ${GRAY}skipping example download.${NC}"
            DOWNLOAD_EXAMPLES="n"
        fi
    fi

    if [[ ! "$DOWNLOAD_EXAMPLES" =~ ^[Nn]$ ]]; then
        echo -e "  ${GRAY}downloading examples...${NC}"

        # Download the zip file
        TEMP_ZIP=$(mktemp)
        curl -L -s -o "$TEMP_ZIP" "https://github.com/Codeplain-ai/plainlang-examples/archive/refs/tags/0.1.zip"

        if [ $? -eq 0 ] && [ -s "$TEMP_ZIP" ]; then
            echo -e "  ${GRAY}extracting to ${EXTRACT_PATH}...${NC}"

            # Extract the zip file
            unzip -q -o "$TEMP_ZIP" -d "$EXTRACT_PATH" 2>/dev/null

            if [ $? -eq 0 ]; then
                # Remove the .gitignore file from the root of the extracted directory
                EXTRACTED_DIR="${EXTRACT_PATH}/plainlang-examples-on-boarding"
                if [ -f "${EXTRACTED_DIR}/.gitignore" ]; then
                    rm -f "${EXTRACTED_DIR}/.gitignore"
                fi

                echo ""
                echo -e "  ${GREEN}✓${NC} examples downloaded successfully!"
                echo ""
                echo -e "  examples are in: ${YELLOW}${EXTRACTED_DIR}${NC}"
                echo ""
            else
                echo -e "  ${RED}✗${NC} failed to extract examples."
            fi

            # Clean up temp file
            rm -f "$TEMP_ZIP"
        else
            echo -e "  ${RED}✗${NC} failed to download examples."
            rm -f "$TEMP_ZIP"
        fi

        echo ""
        read -p "  press [Enter] to continue..." </dev/tty
    fi
fi

# Final message
clear
echo ""
echo -e "${GRAY}────────────────────────────────────────────${NC}"
echo -e "  ${YELLOW}${BOLD}You're all set!${NC}"
echo -e "${GRAY}────────────────────────────────────────────${NC}"
echo ""
echo -e "  thank you for using *codeplain!"
echo ""
echo ""
echo -e "  learn more at ${YELLOW}https://plainlang.org/{NC}"
echo ""
echo -e "  ${GREEN}happy development!${NC} 🚀"
echo ""
