# 🌐 Browser Subagent MCP Server

**Playwright-powered browser automation for Gemini CLI on Kali Linux.**

This MCP (Model Context Protocol) server exposes 24 browser automation tools that Gemini CLI can use to navigate websites, interact with elements, take screenshots, execute JavaScript, and inspect network traffic — all from natural language prompts.

---

## ⚡ Quick Setup (Kali Linux)

```bash
# Clone the repo (if not already done)
git clone <repo-url> && cd tool-bugbounty-antigravity

# Run the automated installer
chmod +x install_kali.sh
./install_kali.sh

# Start Gemini CLI and start browsing!
gemini
```

> The installer handles everything: system deps, Python venv, Playwright + Chromium, and Gemini CLI configuration.

---

## 🔧 Manual Setup

### 1. Install system dependencies

```bash
sudo apt-get install -y libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 \
    libcups2 libdrm2 libdbus-1-3 libxkbcommon0 libxcomposite1 libxdamage1 \
    libxfixes3 libxrandr2 libgbm1 libpango-1.0-0 libcairo2 libasound2 \
    libatspi2.0-0 libwayland-client0 xvfb fonts-liberation
```

### 2. Install Python packages

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements-mcp.txt
playwright install chromium
```

### 3. Configure Gemini CLI

Add the following to `~/.gemini/settings.json`:

```json
{
  "mcpServers": {
    "browser-subagent": {
      "command": "/absolute/path/to/venv/bin/python3",
      "args": ["-m", "browser_mcp_server"],
      "cwd": "/absolute/path/to/tool-bugbounty-antigravity",
      "timeout": 30000,
      "env": {
        "PYTHONPATH": "/absolute/path/to/tool-bugbounty-antigravity"
      }
    }
  }
}
```

> **Important**: Replace `/absolute/path/to/` with your actual project path.

### 4. Verify

```bash
# Test MCP server starts
source venv/bin/activate
python -m browser_mcp_server
# Should hang waiting for stdin (Ctrl+C to stop)

# Or test via Gemini CLI
gemini
> Navigate to https://example.com and tell me the title
```

---

## 🛠 Available Tools (24)

### Navigation
| Tool | Description |
|------|-------------|
| `browser_navigate` | Navigate to URL, get page title + text |
| `browser_back` | Go back in history |
| `browser_forward` | Go forward in history |

### Interaction
| Tool | Description |
|------|-------------|
| `browser_click` | Click element by selector |
| `browser_fill` | Fill form input |
| `browser_type` | Type text char-by-char (triggers keypress events) |
| `browser_press` | Press keyboard key (`Enter`, `Tab`, `Ctrl+a`, etc.) |
| `browser_hover` | Hover over element |
| `browser_select` | Select option from dropdown |
| `browser_wait` | Wait for selector to appear |

### Content Extraction
| Tool | Description |
|------|-------------|
| `browser_get_text` | Get visible text (full page or element) |
| `browser_get_html` | Get HTML (full page or element) |
| `browser_get_attribute` | Get element attribute (`href`, `src`, etc.) |
| `browser_links` | Extract all links |
| `browser_screenshot` | Screenshot page or element (base64 PNG) |

### JavaScript
| Tool | Description |
|------|-------------|
| `browser_evaluate` | Execute JS in page context |

### Tab Management
| Tool | Description |
|------|-------------|
| `browser_tabs` | List all open tabs |
| `browser_new_tab` | Open new tab |
| `browser_switch_tab` | Switch active tab |
| `browser_close_tab` | Close a tab |

### Inspection
| Tool | Description |
|------|-------------|
| `browser_network_log` | Show captured network requests |
| `browser_console_log` | Show browser console messages |
| `browser_cookies` | Get page cookies |
| `browser_set_cookie` | Set a cookie |

---

## 💡 Example Prompts for Gemini CLI

```
# Basic navigation
"Go to https://example.com and summarize the page"

# Bug bounty recon
"Navigate to https://target.com, list all links, and check for any forms"

# Form interaction
"Go to https://target.com/login, fill username with 'admin' and password with 'test', then click the login button"

# JavaScript analysis
"Navigate to https://target.com and execute: document.querySelectorAll('script[src]').length"

# Network inspection
"Navigate to https://target.com and show me all XHR/fetch requests"

# Cookie inspection
"Go to https://target.com and show me all cookies"

# Screenshot
"Navigate to https://target.com and take a full-page screenshot"
```

---

## 🏗 Architecture

```
Gemini CLI  ←─ stdio ─→  MCP Server (FastMCP)
                              │
                         BrowserManager
                              │
                      Playwright + Chromium
                              │
                          Web Pages
```

- **stdio transport**: Gemini CLI spawns the MCP server as a subprocess
- **Lazy initialization**: Browser only launches on first tool call
- **Multi-tab**: Full tab management with independent network/console logs
- **Headless**: Runs without GUI (perfect for SSH/terminal sessions)

---

## 📁 File Structure

```
browser_mcp_server/
├── __init__.py          # Package marker
├── __main__.py          # Entry point (python -m browser_mcp_server)
├── server.py            # MCP server + 24 tool definitions
├── browser_manager.py   # Playwright lifecycle + tab management
└── utils.py             # HTML cleanup, URL validation, formatters
```

---

## 🔍 Troubleshooting

| Issue | Solution |
|-------|----------|
| Chromium won't launch | Run `sudo apt-get install -y libnss3 libgbm1 libasound2` |
| Permission denied | Run `chmod +x install_kali.sh` |
| MCP server not detected | Verify paths in `~/.gemini/settings.json` are absolute |
| Timeout errors | Increase `timeout` in settings.json (default: 30000ms) |
| Headless not working via SSH | Install `xvfb` and use `xvfb-run` prefix |
