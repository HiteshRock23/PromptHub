from playwright.sync_api import sync_playwright

def verify_layout():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            print("Navigating to Hub...")
            page.goto("http://localhost:3000/hub/")
            page.wait_for_load_state("networkidle")

            # Switch to Prompts tab to see the grid
            print("Switching to Prompts tab...")
            page.click("#tab-prompts")
            page.wait_for_timeout(500) # Wait for tab switch

            print("Taking screenshot...")
            page.screenshot(path="verification_prompts_grid.png", full_page=True)
            print("Screenshot saved as verification_prompts_grid.png")

        except Exception as e:
            print(f"Error: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    verify_layout()
