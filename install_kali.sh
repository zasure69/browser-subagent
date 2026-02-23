#!/usr/bin/env bash
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Browser Subagent MCP Server — Kali Linux Installer
#  Installs all dependencies and configures Gemini CLI integration
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${CYAN}"
echo "╔══════════════════════════════════════════════════════════╗"
echo "║   Browser Subagent MCP Server — Kali Linux Installer    ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# ── Step 1: System Dependencies ──────────────────────────────
echo -e "${YELLOW}[1/5] Installing system dependencies for Chromium...${NC}"
sudo apt-get update -qq || echo -e "${YELLOW}  ⚠ apt-get update had warnings (non-critical, continuing...)${NC}"
sudo apt-get install -y -qq \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2t64 \
    libatspi2.0-0 \
    libwayland-client0 \
    xvfb \
    fonts-liberation \
    fonts-noto-color-emoji \
    2>/dev/null

echo -e "${GREEN}  ✓ System dependencies installed${NC}"

# ── Step 2: Python Virtual Environment ───────────────────────
echo -e "${YELLOW}[2/5] Setting up Python virtual environment...${NC}"

VENV_DIR="${SCRIPT_DIR}/venv"

if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
    echo -e "${GREEN}  ✓ Virtual environment created at ${VENV_DIR}${NC}"
else
    echo -e "${GREEN}  ✓ Virtual environment already exists${NC}"
fi

# Activate venv
source "${VENV_DIR}/bin/activate"

# ── Step 3: Install Python Dependencies ──────────────────────
echo -e "${YELLOW}[3/5] Installing Python dependencies...${NC}"
pip install --upgrade pip -q
pip install -r "${SCRIPT_DIR}/requirements-mcp.txt" -q

echo -e "${GREEN}  ✓ Python dependencies installed${NC}"

# ── Step 4: Install Playwright Chromium ──────────────────────
echo -e "${YELLOW}[4/5] Installing Playwright Chromium browser...${NC}"
playwright install chromium
echo -e "${GREEN}  ✓ Chromium installed${NC}"

# ── Step 5: Configure Gemini CLI ─────────────────────────────
echo -e "${YELLOW}[5/5] Configuring Gemini CLI integration...${NC}"

GEMINI_DIR="$HOME/.gemini"
SETTINGS_FILE="${GEMINI_DIR}/settings.json"

mkdir -p "$GEMINI_DIR"

# Build the MCP server configuration
MCP_CONFIG=$(cat <<EOF
{
  "mcpServers": {
    "browser-subagent": {
      "command": "${VENV_DIR}/bin/python3",
      "args": ["-m", "browser_mcp_server"],
      "cwd": "${SCRIPT_DIR}",
      "timeout": 30000,
      "env": {
        "PYTHONPATH": "${SCRIPT_DIR}"
      }
    }
  }
}
EOF
)

if [ -f "$SETTINGS_FILE" ]; then
    echo -e "${YELLOW}  ⚠ Existing settings.json found at ${SETTINGS_FILE}${NC}"
    echo -e "${YELLOW}    A backup has been created at ${SETTINGS_FILE}.bak${NC}"
    cp "$SETTINGS_FILE" "${SETTINGS_FILE}.bak"
    
    # Check if jq is available for merging
    if command -v jq &> /dev/null; then
        # Merge the MCP server config into existing settings
        EXISTING=$(cat "$SETTINGS_FILE")
        echo "$EXISTING" | jq --argjson mcp "$(echo "$MCP_CONFIG" | jq '.mcpServers')" \
            '.mcpServers = (.mcpServers // {}) + $mcp' > "$SETTINGS_FILE"
        echo -e "${GREEN}  ✓ MCP server config merged into existing settings.json${NC}"
    else
        echo -e "${RED}  ✗ jq not found — cannot auto-merge config${NC}"
        echo -e "${YELLOW}    Please manually add the following to ${SETTINGS_FILE}:${NC}"
        echo ""
        echo "$MCP_CONFIG"
        echo ""
    fi
else
    echo "$MCP_CONFIG" > "$SETTINGS_FILE"
    echo -e "${GREEN}  ✓ Created ${SETTINGS_FILE} with MCP server config${NC}"
fi

# ── Done! ────────────────────────────────────────────────────
echo ""
echo -e "${CYAN}╔══════════════════════════════════════════════════════════╗"
echo -e "║                  Installation Complete!                   ║"
echo -e "╚══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}Usage:${NC}"
echo -e "  1. Start Gemini CLI:  ${CYAN}gemini${NC}"
echo -e "  2. Ask it to browse:  ${CYAN}\"Navigate to https://example.com and tell me the page title\"${NC}"
echo ""
echo -e "${GREEN}Manual test:${NC}"
echo -e "  ${CYAN}source ${VENV_DIR}/bin/activate${NC}"
echo -e "  ${CYAN}python -m browser_mcp_server${NC}"
echo ""
echo -e "${GREEN}Available tools (24):${NC}"
echo -e "  Navigation:  browser_navigate, browser_back, browser_forward"
echo -e "  Interact:    browser_click, browser_fill, browser_type, browser_press,"
echo -e "               browser_hover, browser_select, browser_wait"
echo -e "  Extract:     browser_get_text, browser_get_html, browser_get_attribute,"
echo -e "               browser_links, browser_screenshot"
echo -e "  JavaScript:  browser_evaluate"
echo -e "  Tabs:        browser_tabs, browser_new_tab, browser_switch_tab, browser_close_tab"
echo -e "  Inspect:     browser_network_log, browser_console_log,"
echo -e "               browser_cookies, browser_set_cookie"
echo ""
