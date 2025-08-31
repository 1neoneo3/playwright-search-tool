#!/usr/bin/env python3
"""Basic test script for the search tool."""

import asyncio
from playwright.async_api import async_playwright

async def test_basic_search():
    """Test basic search functionality."""
    print("Starting basic search test...")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=[
                '--no-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage'
            ]
        )
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        page = await context.new_page()
        
        # Add stealth
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
        """)
        
        try:
            # Test Google search
            print("Testing Google search...")
            await page.goto("https://www.google.com/search?q=python+programming")
            await page.wait_for_load_state('networkidle')
            
            # Try different selectors
            selectors = ['#search .g', '.g', 'div[data-ved]', '[data-hveid]']
            results_found = False
            
            for selector in selectors:
                elements = await page.query_selector_all(selector)
                print(f"Selector '{selector}': found {len(elements)} elements")
                
                if len(elements) > 0:
                    results_found = True
                    # Try to extract some info from first few results
                    for i, element in enumerate(elements[:3]):
                        try:
                            # Look for title
                            title_element = await element.query_selector('h3')
                            if title_element:
                                title = await title_element.inner_text()
                                print(f"  Result {i+1}: {title[:50]}...")
                            
                            # Look for link
                            link_element = await element.query_selector('a[href]')
                            if link_element:
                                href = await link_element.get_attribute('href')
                                if href and not href.startswith('#'):
                                    print(f"    URL: {href[:50]}...")
                                    
                        except Exception as e:
                            print(f"    Error extracting from result {i+1}: {e}")
                    break
                    
            if not results_found:
                print("No search results found with any selector")
                
        except Exception as e:
            print(f"Error during search: {e}")
            
        finally:
            await browser.close()
            
    print("Test completed.")

if __name__ == "__main__":
    asyncio.run(test_basic_search())