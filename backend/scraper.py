import os
import asyncio
import requests
from urllib.parse import urljoin
from pathlib import Path
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from tqdm import tqdm

DOWNLOAD_DIR = "firmware_downloads"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 " \
             "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"


def download_file_requests(url: str, directory: str):
    try:
        filename = url.split("/")[-1].split("?")[0] or "firmware.bin"
        filepath = os.path.join(directory, filename)
        os.makedirs(directory, exist_ok=True)

        headers = {"User-Agent": USER_AGENT}
        print(f"[*] Downloading via requests -> {url}")
        with requests.get(url, stream=True, headers=headers, timeout=60) as r:
            r.raise_for_status()
            total = int(r.headers.get("content-length", 0))
            with open(filepath, "wb") as f, tqdm(
                desc=filename, total=total, unit="iB", unit_scale=True, unit_divisor=1024
            ) as bar:
                for chunk in r.iter_content(chunk_size=8192):
                    if not chunk:
                        continue
                    f.write(chunk)
                    bar.update(len(chunk))
        print(f"[+] Download complete: {filepath}")
        return filepath
    except Exception as e:
        print(f"[!] requests download failed: {e}")
        return None


async def save_playwright_download(download, directory: str):
    suggested_name = download.suggested_filename or "firmware.bin"
    os.makedirs(directory, exist_ok=True)
    path = os.path.join(directory, suggested_name)
    try:
        await download.save_as(path)
        print(f"[+] Playwright download saved: {path}")
        return path
    except Exception as e:
        print(f"[!] Failed to save playwright download: {e}")
        return None


async def scrape_tp_link(page, base_url):
    print(f"[*] TP-Link: {base_url}")
    try:
        await page.goto(base_url, wait_until="domcontentloaded", timeout=60000)
    except PlaywrightTimeoutError:
        print("[-] Timeout loading page, continuing with what we have...")

    # remove overlay if present (safe)
    try:
        await page.locator(".tp-local-switcher").evaluate("el => el.remove()")
        print("[+] removed tp local switcher if present")
    except Exception:
        pass

    # Click the firmware tab - try a few possible selectors
    firmware_selectors = [
        'button:has-text("Firmware")',
        'a:has-text("Firmware")',
        'text=Firmware'  # fallback
    ]

    for sel in firmware_selectors:
        try:
            await page.locator(sel).first.click(timeout=7000)
            print(f"[+] Clicked firmware tab using selector: {sel}")
            break
        except Exception:
            continue
    else:
        print("[-] Could not find/click a firmware tab. Trying to search for download links directly...")

    # Wait a little for content to render
    await asyncio.sleep(1.5)

    # Strategy A: look for direct download anchor with .zip/.bin/.img etc.
    anchor_candidates = page.locator("a")
    try:
        anchors = await anchor_candidates.element_handles()
    except Exception:
        anchors = []

    for a in anchors:
        try:
            href = await a.get_attribute("href")
            if not href:
                continue
            lower = href.lower()
            if any(ext in lower for ext in [".zip", ".bin", ".img", ".tar", ".tar.gz", ".tgz", ".exe"]):
                resolved = urljoin(base_url, href)
                print(f"[*] Found candidate href: {resolved}")
                return download_file_requests(resolved, DOWNLOAD_DIR)
        except Exception:
            continue

    # Strategy B: attempt to click known download buttons and capture download event
    download_button_selectors = [
        "a:has-text('Download')",
        "a.tp-button:has-text('Download')",
        "button:has-text('Download')",
        "a:has-text('Firmware Download')",
    ]

    for sel in download_button_selectors:
        try:
            btn = page.locator(sel).first
            if await btn.count() == 0:
                continue

            print(f"[*] Attempting to click download button: {sel} and awaiting download event...")
            try:
                async with page.expect_download(timeout=20000) as download_info:
                    await btn.click()
                download = await download_info.value
                return await save_playwright_download(download, DOWNLOAD_DIR)
            except PlaywrightTimeoutError:
                # If no download event, maybe it navigated to a link; try reading href
                href = await btn.get_attribute("href")
                if href:
                    resolved = urljoin(base_url, href)
                    print(f"[*] Click didn't emit download event but href found: {resolved}")
                    return download_file_requests(resolved, DOWNLOAD_DIR)
                else:
                    print("[!] Clicked button but no download event or href found; trying next selector.")
                    continue
        except Exception as e:
            print(f"[-] Selector {sel} failed: {e}")
            continue

    # Strategy C: search page text for direct links (quick fallback)
    try:
        content = await page.content()
        for token in [".zip", ".bin", ".img", ".tar", ".tgz"]:
            if token in content.lower():
                # crude extraction - find href around token
                import re
                matches = re.findall(r'href=["\']([^"\']+%s[^"\']*)["\']' % token, content, flags=re.IGNORECASE)
                if matches:
                    candidate = urljoin(base_url, matches[0])
                    print(f"[*] Found link in page source: {candidate}")
                    return download_file_requests(candidate, DOWNLOAD_DIR)
    except Exception:
        pass

    print("[!] TP-Link: could not find a firmware download using current heuristics.")
    return None


async def scrape_netgear(page, base_url):
    print(f"[*] Netgear: {base_url}")
    try:
        await page.goto(base_url, wait_until="load", timeout=90000)
    except PlaywrightTimeoutError:
        print("[-] Timeout loading Netgear page, continuing...")

    # accept cookies if present (try multiple texts)
    for text in ("Accept All Cookies", "Accept Cookies", "Agree"):
        try:
            btn = page.locator(f'button:has-text("{text}")')
            if await btn.count() > 0:
                await btn.first.click(timeout=3000)
                print(f"[+] Clicked cookie button: {text}")
                break
        except Exception:
            pass

    # Look for download list items that include "Firmware" or "Download"
    candidates = [
        "li:has-text('Firmware') a:has-text('Download')",
        "a:has-text('Download')",
        "a[href*='.zip']",
        "a[href*='.img']",
        "a[href*='/downloads/']",
    ]

    for sel in candidates:
        try:
            link = page.locator(sel).first
            if await link.count() == 0:
                continue

            # first try to capture a download event on click
            try:
                async with page.expect_download(timeout=15000) as download_info:
                    await link.click()
                download = await download_info.value
                return await save_playwright_download(download, DOWNLOAD_DIR)
            except PlaywrightTimeoutError:
                href = await link.get_attribute("href")
                if href:
                    resolved = urljoin(base_url, href)
                    print(f"[*] Found href for Netgear: {resolved}")
                    return download_file_requests(resolved, DOWNLOAD_DIR)
                else:
                    continue
        except Exception as e:
            print(f"[-] Candidate selector {sel} failed: {e}")
            continue

    # fallback: find anchors by extension in page source
    try:
        content = await page.content()
        import re
        matches = re.findall(r'href=["\']([^"\']+\.(zip|bin|img|tar|tgz|exe))["\']', content, flags=re.IGNORECASE)
        if matches:
            candidate = urljoin(base_url, matches[0][0])
            print(f"[*] Found candidate in source: {candidate}")
            return download_file_requests(candidate, DOWNLOAD_DIR)
    except Exception:
        pass

    print("[!] Netgear: could not locate firmware download with current heuristics.")
    return None

async def run_scraper(url):
    """
    This is the main function that app.py imports and calls.
    It orchestrates the entire scraping process.
    """
    print(f"\n--- [Scraper Module] Starting for URL: {url} ---")
    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
            context = await browser.new_context(user_agent=USER_AGENT)
            page = await context.new_page()

            result_path = None
            if "tp-link.com" in url.lower():
                result_path = await scrape_tp_link(page, url)
            elif "netgear.com" in url.lower():
                result_path = await scrape_netgear(page, url)
            else:
                return {"status": "error", "message": f"Manufacturer not supported for URL: {url}"}
        finally:
            if 'browser' in locals() and browser:
                await browser.close()
    
        if result_path:
            # IMPORTANT: Return the simple filename for the redirect
            return {"status": "success", "fileName": os.path.basename(result_path), "message": f"Download complete: {os.path.basename(result_path)}"}
        else:
            return {"status": "error", "message": "Could not find a downloadable firmware file on the page."}


async def main():
    tp_link_url = "https://www.tp-link.com/us/support/download/archer-c7/"
    netgear_url = "https://www.netgear.com/support/product/r7000#download"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        context = await browser.new_context(user_agent=USER_AGENT)
        page = await context.new_page()

        print("\n--- Starting TP-Link Scraper ---")
        await scrape_tp_link(page, tp_link_url)

        print("\n--- Starting Netgear Scraper ---")
        await scrape_netgear(page, netgear_url)

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())