"""
Browser Manager — handles Playwright browser lifecycle, tab management,
network logging, and console message capture.
"""

import asyncio
import logging
from typing import Optional
from dataclasses import dataclass, field
from playwright.async_api import async_playwright, Browser, BrowserContext, Page, Playwright


logger = logging.getLogger("browser-mcp")


@dataclass
class TabInfo:
    """Metadata about an open browser tab."""
    id: int
    page: Page
    title: str = ""
    url: str = ""


class BrowserManager:
    """
    Manages a single Playwright browser instance with multi-tab support,
    network request logging, and console message capture.
    
    The browser is lazily initialized on the first tool call.
    """

    def __init__(self, headless: bool = True):
        self.headless = headless
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._tabs: list[TabInfo] = []
        self._active_tab_id: int = 0
        self._next_tab_id: int = 1
        self._network_log: list[dict] = []
        self._console_log: list[dict] = []
        self._initialized = False

    # ── Lifecycle ──────────────────────────────────────────────

    async def ensure_browser(self) -> Page:
        """Initialize browser if not yet started, return the active page."""
        if not self._initialized:
            await self._start()
        
        if not self._tabs:
            await self.new_tab()
        
        return self.active_page

    async def _start(self):
        """Launch Playwright and Chromium."""
        logger.info("Launching browser...")
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=self.headless,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--disable-web-security',
                '--allow-running-insecure-content',
                '--disable-http2',  # Fix ERR_HTTP2_PROTOCOL_ERROR
                '--disable-blink-features=AutomationControlled',  # Anti-bot detection
            ]
        )
        self._context = await self._browser.new_context(
            user_agent=(
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
                '(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
            ),
            viewport={'width': 1920, 'height': 1080},
            ignore_https_errors=True,
            locale='en-US',
            timezone_id='America/New_York',
            extra_http_headers={
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Upgrade-Insecure-Requests': '1',
            },
        )
        # Stealth: override navigator properties to avoid bot detection
        await self._context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
            window.chrome = { runtime: {} };
        """)
        self._initialized = True
        logger.info("Browser launched successfully")

    async def shutdown(self):
        """Gracefully close browser and Playwright."""
        logger.info("Shutting down browser...")
        try:
            if self._context:
                await self._context.close()
            if self._browser:
                await self._browser.close()
            if self._playwright:
                await self._playwright.stop()
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
        finally:
            self._tabs.clear()
            self._initialized = False
            logger.info("Browser shut down")

    # ── Active Page ────────────────────────────────────────────

    @property
    def active_page(self) -> Page:
        """Return the currently active page."""
        for tab in self._tabs:
            if tab.id == self._active_tab_id:
                return tab.page
        if self._tabs:
            self._active_tab_id = self._tabs[0].id
            return self._tabs[0].page
        raise RuntimeError("No tabs are open")

    # ── Tab Management ─────────────────────────────────────────

    async def new_tab(self, url: Optional[str] = None) -> TabInfo:
        """Open a new tab, optionally navigating to a URL."""
        if not self._initialized:
            await self._start()

        page = await self._context.new_page()
        
        # Attach event listeners
        page.on("console", lambda msg: self._on_console(msg))
        page.on("request", lambda req: self._on_request(req))
        page.on("response", lambda res: self._on_response(res))

        tab_id = self._next_tab_id
        self._next_tab_id += 1

        tab = TabInfo(id=tab_id, page=page)
        self._tabs.append(tab)
        self._active_tab_id = tab_id

        if url:
            await page.goto(url, wait_until='domcontentloaded', timeout=50000)
            tab.title = await page.title()
            tab.url = page.url

        logger.info(f"Opened new tab #{tab_id}" + (f" → {url}" if url else ""))
        return tab

    async def close_tab(self, tab_id: Optional[int] = None) -> str:
        """Close a tab by id. Defaults to the active tab."""
        target_id = tab_id or self._active_tab_id

        for i, tab in enumerate(self._tabs):
            if tab.id == target_id:
                await tab.page.close()
                self._tabs.pop(i)

                # Switch to another tab if available
                if self._tabs and self._active_tab_id == target_id:
                    self._active_tab_id = self._tabs[-1].id

                logger.info(f"Closed tab #{target_id}")
                return f"Tab #{target_id} closed"

        return f"Tab #{target_id} not found"

    async def switch_tab(self, tab_id: int) -> str:
        """Switch to a specific tab by id."""
        for tab in self._tabs:
            if tab.id == tab_id:
                self._active_tab_id = tab_id
                tab.title = await tab.page.title()
                tab.url = tab.page.url
                return f"Switched to tab #{tab_id}: {tab.title} ({tab.url})"
        return f"Tab #{tab_id} not found"

    async def list_tabs(self) -> list[dict]:
        """List all open tabs with their metadata."""
        result = []
        for tab in self._tabs:
            try:
                tab.title = await tab.page.title()
                tab.url = tab.page.url
            except Exception:
                pass
            result.append({
                'id': tab.id,
                'title': tab.title,
                'url': tab.url,
                'active': tab.id == self._active_tab_id
            })
        return result

    # ── Network & Console Logging ──────────────────────────────

    def _on_console(self, msg):
        """Capture console messages."""
        self._console_log.append({
            'type': msg.type,
            'text': msg.text,
        })
        # Keep last 200 entries
        if len(self._console_log) > 200:
            self._console_log = self._console_log[-200:]

    def _on_request(self, request):
        """Capture network requests."""
        self._network_log.append({
            'method': request.method,
            'url': request.url,
            'resource_type': request.resource_type,
            'status': None,  # Will be updated on response
        })
        # Keep last 500 entries
        if len(self._network_log) > 500:
            self._network_log = self._network_log[-500:]

    def _on_response(self, response):
        """Update network log with response status."""
        url = response.url
        for entry in reversed(self._network_log):
            if entry['url'] == url and entry['status'] is None:
                entry['status'] = response.status
                break

    def get_network_log(self, filter_type: Optional[str] = None) -> list[dict]:
        """
        Get network log entries, optionally filtered by resource type.
        Resource types: document, stylesheet, image, media, font, script, 
        texttrack, xhr, fetch, eventsource, websocket, manifest, other
        """
        if filter_type:
            return [e for e in self._network_log if e.get('resource_type') == filter_type]
        return list(self._network_log)

    def get_console_log(self, filter_type: Optional[str] = None) -> list[dict]:
        """
        Get console log entries, optionally filtered by type.
        Types: log, warning, error, info, debug
        """
        if filter_type:
            return [e for e in self._console_log if e.get('type') == filter_type]
        return list(self._console_log)

    def clear_network_log(self):
        """Clear the network log."""
        self._network_log.clear()

    def clear_console_log(self):
        """Clear the console log."""
        self._console_log.clear()
