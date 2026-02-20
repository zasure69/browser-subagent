"""
Browser Subagent MCP Server
Exposes Playwright browser automation tools via the Model Context Protocol.
Designed for integration with Gemini CLI on Kali Linux.
"""

import asyncio
import json
import logging
import sys
from typing import Optional

from mcp.server.fastmcp import FastMCP

from .browser_manager import BrowserManager
from .utils import (
    clean_text,
    strip_html_tags,
    encode_screenshot,
    validate_url,
    safe_selector,
    truncate_html,
    format_links,
    format_cookies,
    format_network_log,
)

# ── Logging Setup ─────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    stream=sys.stderr,  # MCP uses stdout for protocol, logs go to stderr
)
logger = logging.getLogger("browser-mcp")

# ── MCP Server & Browser ──────────────────────────────────────
mcp = FastMCP(
    "Browser Subagent",
    instructions=(
        "A browser automation subagent powered by Playwright. "
        "Navigate websites, interact with elements, take screenshots, "
        "execute JavaScript, inspect network traffic, and more. "
        "Optimized for bug bounty reconnaissance and web security testing on Kali Linux."
    ),
)

browser = BrowserManager(headless=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  NAVIGATION TOOLS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@mcp.tool()
async def browser_navigate(url: str, wait_until: str = "domcontentloaded") -> str:
    """
    Navigate to a URL and return the page title and text content.
    
    Args:
        url: The URL to navigate to (https:// is added if no scheme)
        wait_until: When to consider navigation done — 'domcontentloaded', 'load', or 'networkidle'
    
    Returns:
        Page title and visible text content
    """
    url = validate_url(url)
    page = await browser.ensure_browser()

    try:
        await page.goto(url, wait_until=wait_until, timeout=30000)
    except Exception as e:
        return f"Navigation error: {e}"

    title = await page.title()
    content = await page.evaluate("() => document.body ? document.body.innerText : ''")
    content = clean_text(content)

    # Update tab info
    for tab in browser._tabs:
        if tab.id == browser._active_tab_id:
            tab.title = title
            tab.url = page.url
            break

    return f"**Page:** {title}\n**URL:** {page.url}\n\n{content}"


@mcp.tool()
async def browser_back() -> str:
    """Navigate back in browser history."""
    page = await browser.ensure_browser()
    try:
        await page.go_back(timeout=10000)
        title = await page.title()
        return f"Navigated back → {title} ({page.url})"
    except Exception as e:
        return f"Cannot go back: {e}"


@mcp.tool()
async def browser_forward() -> str:
    """Navigate forward in browser history."""
    page = await browser.ensure_browser()
    try:
        await page.go_forward(timeout=10000)
        title = await page.title()
        return f"Navigated forward → {title} ({page.url})"
    except Exception as e:
        return f"Cannot go forward: {e}"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  INTERACTION TOOLS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@mcp.tool()
async def browser_click(selector: str) -> str:
    """
    Click an element on the page.
    
    Args:
        selector: CSS selector or XPath of the element to click (e.g. 'button.submit', '#login-btn', '//a[@href="/about"]')
    """
    selector = safe_selector(selector)
    page = await browser.ensure_browser()

    try:
        await page.click(selector, timeout=10000)
        await page.wait_for_load_state("domcontentloaded", timeout=5000)
        title = await page.title()
        return f"Clicked '{selector}' → Page: {title} ({page.url})"
    except Exception as e:
        return f"Click failed on '{selector}': {e}"


@mcp.tool()
async def browser_fill(selector: str, text: str) -> str:
    """
    Fill a form input field with text.
    
    Args:
        selector: CSS selector of the input element (e.g. 'input[name="username"]', '#email')
        text: Text to type into the field
    """
    selector = safe_selector(selector)
    page = await browser.ensure_browser()

    try:
        await page.fill(selector, text, timeout=10000)
        return f"Filled '{selector}' with '{text}'"
    except Exception as e:
        return f"Fill failed on '{selector}': {e}"


@mcp.tool()
async def browser_select(selector: str, value: str) -> str:
    """
    Select an option from a <select> dropdown.
    
    Args:
        selector: CSS selector of the <select> element
        value: The value or label of the option to select
    """
    selector = safe_selector(selector)
    page = await browser.ensure_browser()

    try:
        await page.select_option(selector, value, timeout=10000)
        return f"Selected '{value}' in '{selector}'"
    except Exception as e:
        return f"Select failed on '{selector}': {e}"


@mcp.tool()
async def browser_type(selector: str, text: str, delay: int = 50) -> str:
    """
    Type text into an element character by character (simulates real typing).
    Use this instead of browser_fill when the page has keypress event handlers.
    
    Args:
        selector: CSS selector of the input element
        text: Text to type
        delay: Delay between keystrokes in milliseconds (default 50)
    """
    selector = safe_selector(selector)
    page = await browser.ensure_browser()

    try:
        await page.type(selector, text, delay=delay, timeout=10000)
        return f"Typed '{text}' into '{selector}'"
    except Exception as e:
        return f"Type failed on '{selector}': {e}"


@mcp.tool()
async def browser_press(key: str) -> str:
    """
    Press a keyboard key (e.g. 'Enter', 'Tab', 'Escape', 'ArrowDown', 'Control+a').
    
    Args:
        key: Key to press — supports key names and combinations like 'Control+c'
    """
    page = await browser.ensure_browser()
    try:
        await page.keyboard.press(key)
        return f"Pressed key: {key}"
    except Exception as e:
        return f"Key press failed: {e}"


@mcp.tool()
async def browser_hover(selector: str) -> str:
    """
    Hover over an element to trigger hover effects, tooltips, or dropdown menus.
    
    Args:
        selector: CSS selector of the element to hover
    """
    selector = safe_selector(selector)
    page = await browser.ensure_browser()

    try:
        await page.hover(selector, timeout=10000)
        return f"Hovering over '{selector}'"
    except Exception as e:
        return f"Hover failed on '{selector}': {e}"


@mcp.tool()
async def browser_wait(selector: str, timeout: int = 10000, state: str = "visible") -> str:
    """
    Wait for an element to appear on the page.
    
    Args:
        selector: CSS selector to wait for
        timeout: Max wait time in milliseconds (default 10000)
        state: Element state to wait for — 'visible', 'hidden', 'attached', 'detached'
    """
    selector = safe_selector(selector)
    page = await browser.ensure_browser()

    try:
        await page.wait_for_selector(selector, timeout=timeout, state=state)
        return f"Element '{selector}' is now {state}"
    except Exception as e:
        return f"Wait failed for '{selector}': {e}"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  CONTENT EXTRACTION TOOLS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@mcp.tool()
async def browser_get_text(selector: Optional[str] = None) -> str:
    """
    Get visible text content from the page or a specific element.
    
    Args:
        selector: Optional CSS selector. If omitted, returns the full page text.
    """
    page = await browser.ensure_browser()

    try:
        if selector:
            selector = safe_selector(selector)
            text = await page.eval_on_selector(selector, "el => el.innerText")
        else:
            text = await page.evaluate("() => document.body ? document.body.innerText : ''")
        return clean_text(text)
    except Exception as e:
        return f"Text extraction failed: {e}"


@mcp.tool()
async def browser_get_html(selector: Optional[str] = None, outer: bool = True) -> str:
    """
    Get HTML content of the page or a specific element.
    
    Args:
        selector: Optional CSS selector. If omitted, returns full page HTML.
        outer: If True, includes the element's own tag (outerHTML). If False, only children (innerHTML).
    """
    page = await browser.ensure_browser()

    try:
        if selector:
            selector = safe_selector(selector)
            prop = "outerHTML" if outer else "innerHTML"
            html = await page.eval_on_selector(selector, f"el => el.{prop}")
        else:
            html = await page.content()
        return truncate_html(html)
    except Exception as e:
        return f"HTML extraction failed: {e}"


@mcp.tool()
async def browser_get_attribute(selector: str, attribute: str) -> str:
    """
    Get an attribute value from an element (e.g. href, src, class, data-*, value).
    
    Args:
        selector: CSS selector of the target element
        attribute: Name of the attribute to retrieve
    """
    selector = safe_selector(selector)
    page = await browser.ensure_browser()

    try:
        value = await page.get_attribute(selector, attribute, timeout=5000)
        return f"{attribute}=\"{value}\"" if value is not None else f"Attribute '{attribute}' not found on '{selector}'"
    except Exception as e:
        return f"Get attribute failed: {e}"


@mcp.tool()
async def browser_links() -> str:
    """
    Extract all links (<a> tags) from the current page.
    Returns a numbered list of links with their text and href.
    """
    page = await browser.ensure_browser()

    try:
        links = await page.evaluate("""() => {
            return Array.from(document.querySelectorAll('a[href]')).map(a => ({
                text: a.innerText.trim().substring(0, 100),
                href: a.href
            })).filter(l => l.href && !l.href.startsWith('javascript:'));
        }""")
        return format_links(links)
    except Exception as e:
        return f"Link extraction failed: {e}"


@mcp.tool()
async def browser_screenshot(
    selector: Optional[str] = None,
    full_page: bool = False
) -> str:
    """
    Take a screenshot of the page or a specific element.
    Returns base64-encoded PNG image data.
    
    Args:
        selector: Optional CSS selector to screenshot a specific element
        full_page: If True, captures the entire scrollable page (ignored if selector is set)
    """
    page = await browser.ensure_browser()

    try:
        if selector:
            selector = safe_selector(selector)
            element = await page.query_selector(selector)
            if not element:
                return f"Element '{selector}' not found for screenshot"
            screenshot = await element.screenshot(type='png')
        else:
            screenshot = await page.screenshot(type='png', full_page=full_page)

        b64 = encode_screenshot(screenshot)
        size_kb = len(screenshot) / 1024
        return f"Screenshot captured ({size_kb:.1f} KB)\n\ndata:image/png;base64,{b64}"
    except Exception as e:
        return f"Screenshot failed: {e}"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  JAVASCRIPT EXECUTION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@mcp.tool()
async def browser_evaluate(script: str) -> str:
    """
    Execute JavaScript in the browser page context and return the result.
    Use this for advanced DOM queries, API calls, or page manipulation.
    
    Args:
        script: JavaScript code to execute. Should be an expression or 
                wrapped in an IIFE: (() => { ... })()
    
    Examples:
        - "document.title"
        - "document.querySelectorAll('input').length"
        - "(() => { let forms = document.forms; return forms.length; })()"
    """
    page = await browser.ensure_browser()

    try:
        result = await page.evaluate(script)
        if isinstance(result, (dict, list)):
            return json.dumps(result, indent=2, ensure_ascii=False)
        return str(result) if result is not None else "undefined"
    except Exception as e:
        return f"JavaScript evaluation error: {e}"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  TAB MANAGEMENT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@mcp.tool()
async def browser_tabs() -> str:
    """List all open browser tabs with their id, title, URL, and active status."""
    tabs = await browser.list_tabs()
    if not tabs:
        return "No tabs are open."

    lines = []
    for t in tabs:
        marker = " ← active" if t['active'] else ""
        lines.append(f"  Tab #{t['id']}: {t['title'] or '(untitled)'} — {t['url'] or 'about:blank'}{marker}")
    return "Open tabs:\n" + '\n'.join(lines)


@mcp.tool()
async def browser_new_tab(url: Optional[str] = None) -> str:
    """
    Open a new browser tab.
    
    Args:
        url: Optional URL to navigate to in the new tab
    """
    tab = await browser.new_tab(url)
    return f"Opened new tab #{tab.id}" + (f" → {tab.url}" if tab.url else "")


@mcp.tool()
async def browser_switch_tab(tab_id: int) -> str:
    """
    Switch to a specific browser tab.
    
    Args:
        tab_id: The tab ID (use browser_tabs to see available IDs)
    """
    return await browser.switch_tab(tab_id)


@mcp.tool()
async def browser_close_tab(tab_id: Optional[int] = None) -> str:
    """
    Close a browser tab.
    
    Args:
        tab_id: The tab ID to close. If omitted, closes the active tab.
    """
    return await browser.close_tab(tab_id)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  NETWORK & COOKIES & CONSOLE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@mcp.tool()
async def browser_network_log(resource_type: Optional[str] = None, clear: bool = False) -> str:
    """
    Get captured network requests and their responses.
    
    Args:
        resource_type: Filter by type — 'xhr', 'fetch', 'document', 'script', 'stylesheet', 'image', etc.
        clear: If True, clear the log after reading
    
    Returns:
        List of network requests with method, status, type, and URL
    """
    entries = browser.get_network_log(filter_type=resource_type)
    result = format_network_log(entries)
    if clear:
        browser.clear_network_log()
    return result


@mcp.tool()
async def browser_console_log(log_type: Optional[str] = None, clear: bool = False) -> str:
    """
    Get browser console messages (log, warning, error, info).
    
    Args:
        log_type: Filter by type — 'log', 'warning', 'error', 'info', 'debug'
        clear: If True, clear the log after reading
    """
    entries = browser.get_console_log(filter_type=log_type)

    if not entries:
        return "No console messages captured."

    lines = []
    for e in entries[-100:]:
        prefix = {'error': '❌', 'warning': '⚠️', 'info': 'ℹ️'}.get(e['type'], '📝')
        lines.append(f"  {prefix} [{e['type']}] {e['text']}")

    result = f"Console messages ({len(entries)} total, showing last {min(len(entries), 100)}):\n" + '\n'.join(lines)
    if clear:
        browser.clear_console_log()
    return result


@mcp.tool()
async def browser_cookies(url: Optional[str] = None) -> str:
    """
    Get cookies for the current page or a specific URL.
    
    Args:
        url: Optional URL to get cookies for. Defaults to current page URL.
    """
    page = await browser.ensure_browser()

    try:
        if url:
            cookies = await browser._context.cookies(url)
        else:
            cookies = await browser._context.cookies(page.url)
        return format_cookies(cookies)
    except Exception as e:
        return f"Failed to get cookies: {e}"


@mcp.tool()
async def browser_set_cookie(
    name: str,
    value: str,
    domain: Optional[str] = None,
    path: str = "/",
    secure: bool = False,
    http_only: bool = False,
) -> str:
    """
    Set a cookie in the browser context.
    
    Args:
        name: Cookie name
        value: Cookie value
        domain: Cookie domain (defaults to current page domain)
        path: Cookie path (default '/')
        secure: Whether the cookie requires HTTPS
        http_only: Whether the cookie is HTTP-only (not accessible via JS)
    """
    page = await browser.ensure_browser()

    if not domain:
        from urllib.parse import urlparse
        parsed = urlparse(page.url)
        domain = parsed.hostname or 'localhost'

    try:
        await browser._context.add_cookies([{
            'name': name,
            'value': value,
            'domain': domain,
            'path': path,
            'secure': secure,
            'httpOnly': http_only,
            'url': page.url,
        }])
        return f"Cookie set: {name}={value} (domain={domain}, path={path})"
    except Exception as e:
        return f"Failed to set cookie: {e}"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  SERVER ENTRY POINT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def run():
    """Start the MCP server using stdio transport."""
    logger.info("Starting Browser Subagent MCP Server...")
    mcp.run(transport="stdio")
