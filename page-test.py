import asyncio
import sys

from playwright.async_api import async_playwright
from playwright_stealth import Stealth  # type: ignore[reportMissingTypeStubs]


def _write_to_file(filename: str, content: str) -> None:
    """Synchronously writes content to a file."""
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)


async def main():
    if len(sys.argv) < 2:
        print("Usage: python page-test.py <URL>")
        return

    url = sys.argv[1]

    async with async_playwright() as p:
        browser = await p.chromium.launch(channel="chrome", headless=False)
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/125.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1920, "height": 1080},
        )
        stealth = Stealth()
        # Apply stealth patches to the context
        await stealth.apply_stealth_async(context)

        page = await context.new_page()

        print(f"Navigating to {url}...")
        await page.goto(url, wait_until="domcontentloaded")

        print("Waiting for 10 seconds...")
        await page.wait_for_timeout(10000)

        print("Saving page content to page-test.html...")
        content = await page.content()
        await asyncio.to_thread(_write_to_file, "page-test.html", content)

        await browser.close()
        print("Done.")


if __name__ == "__main__":
    asyncio.run(main())
