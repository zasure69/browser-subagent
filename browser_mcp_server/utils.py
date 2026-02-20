"""
Utility functions for the Browser MCP Server.
HTML cleanup, screenshot handling, URL validation.
"""

import base64
import re
from urllib.parse import urlparse, urljoin
from typing import Optional


def clean_text(html_text: str, max_length: int = 50000) -> str:
    """
    Clean extracted text content: normalize whitespace, remove excessive blank lines.
    """
    if not html_text:
        return ""
    
    # Normalize line endings
    text = html_text.replace('\r\n', '\n').replace('\r', '\n')
    
    # Remove excessive blank lines (keep max 2 consecutive)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Remove leading/trailing whitespace from each line
    lines = [line.strip() for line in text.split('\n')]
    text = '\n'.join(lines)
    
    # Trim to max length
    if len(text) > max_length:
        text = text[:max_length] + f"\n\n... [Truncated at {max_length} characters]"
    
    return text.strip()


def strip_html_tags(html: str) -> str:
    """
    Strip HTML tags and return plain text.
    """
    if not html:
        return ""
    
    # Remove script and style elements entirely
    html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
    
    # Replace block-level tags with newlines
    block_tags = r'</?(div|p|br|h[1-6]|li|tr|td|th|blockquote|pre|hr|section|article|header|footer|nav|main)[^>]*>'
    html = re.sub(block_tags, '\n', html, flags=re.IGNORECASE)
    
    # Remove remaining tags
    html = re.sub(r'<[^>]+>', '', html)
    
    # Decode common HTML entities
    html = html.replace('&amp;', '&')
    html = html.replace('&lt;', '<')
    html = html.replace('&gt;', '>')
    html = html.replace('&quot;', '"')
    html = html.replace('&#39;', "'")
    html = html.replace('&nbsp;', ' ')
    
    return clean_text(html)


def encode_screenshot(screenshot_bytes: bytes) -> str:
    """
    Encode screenshot bytes to base64 string.
    """
    return base64.b64encode(screenshot_bytes).decode('utf-8')


def validate_url(url: str) -> str:
    """
    Validate and normalize a URL. Adds https:// if no scheme is provided.
    
    Returns:
        Normalized URL string
        
    Raises:
        ValueError: If URL is invalid
    """
    if not url or not url.strip():
        raise ValueError("URL cannot be empty")
    
    url = url.strip()
    
    # Add scheme if missing
    if not url.startswith(('http://', 'https://', 'file://')):
        url = 'https://' + url
    
    parsed = urlparse(url)
    
    if not parsed.netloc and not parsed.scheme == 'file':
        raise ValueError(f"Invalid URL: {url}")
    
    return url


def safe_selector(selector: str) -> str:
    """
    Sanitize a CSS/XPath selector string.
    """
    if not selector or not selector.strip():
        raise ValueError("Selector cannot be empty")
    return selector.strip()


def truncate_html(html: str, max_length: int = 100000) -> str:
    """
    Truncate HTML content to a reasonable size for LLM consumption.
    """
    if not html:
        return ""
    if len(html) > max_length:
        return html[:max_length] + f"\n<!-- Truncated at {max_length} characters -->"
    return html


def format_links(links: list[dict]) -> str:
    """
    Format extracted links into a readable text format.
    """
    if not links:
        return "No links found on the page."
    
    result = []
    for i, link in enumerate(links, 1):
        text = link.get('text', '').strip() or '[no text]'
        href = link.get('href', '')
        result.append(f"{i}. [{text}]({href})")
    
    return '\n'.join(result)


def format_cookies(cookies: list[dict]) -> str:
    """
    Format cookies into a readable text format.
    """
    if not cookies:
        return "No cookies found."
    
    result = []
    for cookie in cookies:
        name = cookie.get('name', '')
        value = cookie.get('value', '')
        domain = cookie.get('domain', '')
        path = cookie.get('path', '/')
        secure = '🔒' if cookie.get('secure') else ''
        httponly = '🚫JS' if cookie.get('httpOnly') else ''
        result.append(f"• {name}={value[:50]}{'...' if len(value) > 50 else ''} "
                      f"(domain={domain}, path={path}) {secure}{httponly}")
    
    return '\n'.join(result)


def format_network_log(entries: list[dict], max_entries: int = 50) -> str:
    """
    Format network log entries into readable text.
    """
    if not entries:
        return "No network requests captured."
    
    entries = entries[-max_entries:]  # Show most recent
    
    result = [f"Showing last {len(entries)} requests:\n"]
    for entry in entries:
        method = entry.get('method', 'GET')
        url = entry.get('url', '')
        status = entry.get('status', '?')
        resource_type = entry.get('resource_type', '')
        
        # Truncate long URLs
        display_url = url if len(url) <= 100 else url[:97] + '...'
        result.append(f"  {method} {status} [{resource_type}] {display_url}")
    
    return '\n'.join(result)
