from playwright.sync_api import sync_playwright
import time

# --- MISSION CONFIGURATION ---
ROUTER_URL = "http://192.168.1.1"
LOGIN_USER = "customer"
LOGIN_PASS = "celcomdigi123"

# The Configuration we want to apply
NEW_SSID = "NS Room 8017"
NEW_WIFI_PASS = "darktalent2024!"
# -----------------------------

def run():
    print("🚀 INITIALIZING ROUTER FACTORY...")
    print(f"🎯 Target: {ROUTER_URL}")

    with sync_playwright() as p:
        # headless=False so you can WATCH the robot work
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        try:
            # 1. BREACH THE GATE (Login)
            print("--------------------------------")
            print("Step 1: Approaching Login Page...")
            page.goto(ROUTER_URL)

            # Wait for the login box (TP-Link usually has username & password or just password)
            # Based on your notes, it asks for BOTH.
            # We use generic selectors for login first, or fallbacks
            try:
                print("🔑 Attempting Login...")
                # Try to fill username if it exists
                if page.is_visible("input#userName"):
                    page.fill("input#userName", LOGIN_USER)
                elif page.is_visible("input.text-text"): # Common TP-Link class
                    page.fill("input.text-text", LOGIN_USER)

                # Fill Password (looking for type='password')
                page.fill("input[type='password']", LOGIN_PASS)

                # Smash Enter
                page.keyboard.press("Enter")
            except Exception as e:
                print(f"⚠️ Login Hiccup: {e}")

            # 2. NAVIGATE TO WIRELESS (The Navigation)
            print("Step 2: Navigating to Wireless Settings...")
            # We wait for the dashboard to load.
            page.wait_for_timeout(3000)

            # Click "Wireless" or "Basic" tab.
            # This uses a text selector which is very robust.
            if page.is_visible("text=Wireless"):
                page.click("text=Wireless")
            elif page.is_visible("text=Basic"):
                page.click("text=Basic")

            # 3. CONFIGURE SETTINGS (The Payload)
            print("Step 3: Injecting Configuration...")

            # Wait for the SSID box to appear (The ID you found!)
            page.wait_for_selector("#ssid_2g", state="visible")

            # A. Change SSID
            print(f"✏️  Renaming SSID to: {NEW_SSID}")
            page.fill("#ssid_2g", "") # Clear it first
            page.fill("#ssid_2g", NEW_SSID)

            # B. Change Password
            print(f"🔐 Setting Password to: {NEW_WIFI_PASS}")
            page.fill("#wpa2PersonalPwd_2g", "") # Clear it first
            page.fill("#wpa2PersonalPwd_2g", NEW_WIFI_PASS)

            # 4. EXECUTE (Save)
            print("Step 4: SAVING CONFIGURATION...")
            page.click("#save_2g")

            print("--------------------------------")
            print("✅ MISSION SUCCESS: Router Configured.")
            print("⚠️ Router is now rebooting. You will lose connection.")
            print("--------------------------------")

            # Keep window open for 5s to celebrate
            time.sleep(5)

        except Exception as e:
            print(f"❌ MISSION FAILED: {e}")
            # Keep window open to debug
            time.sleep(30)

        browser.close()

if __name__ == "__main__":
    run()