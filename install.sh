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
