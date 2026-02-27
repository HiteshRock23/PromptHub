from playwright.sync_api import sync_playwright

def verify_layout():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            print("Navigating to Hub...")
            page.goto("http://localhost:3000/hub/")
            page.wait_for_load_state("networkidle")

            print("Checking for Navbar...")
            page.wait_for_selector(".site-header")

            print("Checking for Hero...")
            page.wait_for_selector(".hero-section")

            print("Checking for Stats...")
            page.wait_for_selector(".stats-section")

            print("Taking screenshot...")
            page.screenshot(path="verification_layout.png", full_page=True)
            print("Screenshot saved as verification_layout.png")

        except Exception as e:
            print(f"Error: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    verify_layout()
