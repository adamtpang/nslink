from playwright.sync_api import sync_playwright
import time
import re
import os

def save_debug_artifact(page, step_name):
    """Saves a screenshot and HTML dump for debugging."""
    timestamp = int(time.time())
    screenshot_path = f"debug_{step_name}_{timestamp}.png"
    html_path = f"debug_{step_name}_{timestamp}.html"

    try:
        page.screenshot(path=screenshot_path)
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(page.content())
        print(f"   📸 Debug artifacts saved: {screenshot_path}, {html_path}")
    except Exception as e:
        print(f"   ⚠️ Could not save debug artifacts: {e}")

def login_to_router(page, user, password):
    """Helper to handle the login screen."""
    print("   🔑 Attempting Login...")
    try:
        # Wait for any known login field
        try:
            page.wait_for_selector("input[placeholder='Username'], #pc-login-user, input#userName", timeout=5000)
        except:
            print("   ⚠️ Login fields not found immediately. Saving debug info...")
            save_debug_artifact(page, "login_not_found")
            # Continue anyway, might be already logged in?

        if page.is_visible("input[placeholder='Username']"):
            page.fill("input[placeholder='Username']", user)
        elif page.is_visible("#pc-login-user"):
            page.fill("#pc-login-user", user)
        elif page.is_visible("input#userName"):
            page.fill("input#userName", user)

        if page.is_visible("input[type='password']"):
            page.fill("input[type='password']", password)
        elif page.is_visible("#pc-login-password"):
            page.fill("#pc-login-password", password)

        page.keyboard.press("Enter")
        page.wait_for_timeout(1000)

        # Handle "Force Logout" Dialog
        if page.is_visible("text=Only one device can log in at a time"):
            print("   ⚠️ Detected active session. Forcing logout...")
            if page.is_visible("button:has-text('Log in')"):
                page.click("button:has-text('Log in')")

        # VERIFICATION: Check if we are past the login screen
        page.wait_for_timeout(2000)
        if page.is_visible("input[type='password']"):
             print("   ❌ Login failed (Password field still visible).")
             save_debug_artifact(page, "login_failed")
             return False

        print("   ✅ Login successful (probably).")
        return True
    except Exception as e:
        print(f"   ⚠️ Login Hiccup: {e}")
        save_debug_artifact(page, "login_exception")
        return False

def run_wizard_flow(page, config):
    """
    Phase 1: Factory Reset -> Wizard -> Wireless Config
    """
    ROUTER_URL = config.get('router_url', "http://192.168.1.1")
    LOGIN_USER = config['login_user']
    LOGIN_PASS = config['login_pass']
    NEW_SSID = config['new_ssid']
    NEW_WIFI_PASS = config['new_wifi_pass']

    print(f"   🚀 Starting Wizard Flow for {NEW_SSID}...")

    try:
        # 1. Login
        print(f"   🌐 Navigating to {ROUTER_URL}...")
        try:
            page.goto(ROUTER_URL, timeout=10000)
        except Exception as e:
             print(f"   ⚠️ Navigation failed: {e}")
             # Sometimes it loads partial

        page.wait_for_load_state("domcontentloaded")

        if not login_to_router(page, LOGIN_USER, LOGIN_PASS):
            print("   🛑 Login failed. Aborting wizard.")
            return False

        # 2. Handle Wizard Steps (The Golden Path)
        print("   🧙 Running Wizard...")
        page.wait_for_timeout(2000)

        # Step 1: Region Selection
        try:
            # Check if we are actually on the wizard page
            if not page.is_visible("[id='_region']"):
                 print("   ⚠️ Region selector not found. Checking where we are...")
                 save_debug_artifact(page, "pre_region_check")

            page.wait_for_selector("[id='_region']", timeout=5000)
            print("   🌏 Selecting Region: Malaysia...")

            # Click the dropdown to open it
            page.click("[id='_region']")
            page.wait_for_timeout(1000) # Wait for animation

            # Click the option
            # Try multiple selectors for the option to be safe
            try:
                page.locator(".select-option").get_by_text("Malaysia").click()
            except:
                page.get_by_text("Malaysia").click()

            page.wait_for_timeout(1000)

            print("   ➡️ Next (Region)...")
            page.get_by_role("button", name="Next").click()
            page.wait_for_timeout(2000)

            print("   ➡️ Next (Time Zone/Connection Type)...")
            page.get_by_role("button", name="Next").click()
            page.wait_for_timeout(2000)
        except Exception as e:
            print(f"   ⚠️ Region/Timezone step skipped or failed: {e}")
            save_debug_artifact(page, "region_step_fail")

        # Step 3: Wireless Settings
        print("   📶 Configuring Wireless (Dual Band Mode)...")

        # SKIP Band Steering (We want separate names)
        # if page.is_visible(".icon.checkbox-hover-unchecked"):
        #     print("   🔀 Enabling Band Steering (Smart Connect)...")
        #     page.locator(".icon.checkbox-hover-unchecked").click()
        #     page.wait_for_timeout(1000)

        # Wait for textboxes
        try:
            page.wait_for_selector("input[type='text']", timeout=5000)
        except:
             print("   ⚠️ Wireless settings textboxes not found.")
             save_debug_artifact(page, "wireless_step_fail")

        # We expect 4 fields: SSID 2.4, Pass 2.4, SSID 5, Pass 5
        textboxes = page.get_by_role("textbox").all()
        print(f"   Found {len(textboxes)} textboxes.")

        if len(textboxes) >= 4:
            # 2.4GHz
            ssid_24 = f"{NEW_SSID} 2.4Ghz"
            print(f"   ✏️ Setting 2.4GHz SSID: {ssid_24}")
            textboxes[0].fill(ssid_24)

            print(f"   🔐 Setting 2.4GHz Password: {NEW_WIFI_PASS}")
            textboxes[1].fill(NEW_WIFI_PASS)

            # 5GHz
            ssid_5 = f"{NEW_SSID} 5.0Ghz"
            print(f"   ✏️ Setting 5GHz SSID: {ssid_5}")
            textboxes[2].fill(ssid_5)

            print(f"   🔐 Setting 5GHz Password: {NEW_WIFI_PASS}")
            textboxes[3].fill(NEW_WIFI_PASS)
        else:
            print(f"   ⚠️ Unexpected number of textboxes ({len(textboxes)}). Trying generic fill...")
            # Fallback: Fill first SSID/Pass found
            if len(textboxes) >= 1: textboxes[0].fill(NEW_SSID)
            if len(textboxes) >= 2: textboxes[1].fill(NEW_WIFI_PASS)

        # Click Next
        print("   ➡️ Next (Wireless)...")
        page.get_by_role("button", name="Next").click()
        page.wait_for_timeout(2000)

        # Step 4: Summary / Save
        print("   💾 Saving Configuration...")
        if page.is_visible("button:has-text('Next')"):
            page.get_by_role("button", name="Next").click()
        elif page.is_visible("button:has-text('Save')"):
            page.get_by_role("button", name="Save").click()

        page.wait_for_timeout(2000)

        # Step 5: Confirmation Dialog?
        if page.is_visible("button:has-text('OK')"):
            print("   ✅ Clicking OK...")
            page.get_by_role("button", name="OK").click()

        print("   ✅ Wizard Complete. Router should reboot.")
        return True

    except Exception as e:
        print(f"   ❌ Wizard Failed: {e}")
        save_debug_artifact(page, "wizard_fatal_error")
        print("\n   🛑 PAUSING FOR MANUAL INTERVENTION!")
        print("   1. Check the browser window.")
        print("   2. Manually complete the wizard steps.")
        print("   3. Close the browser window to continue (or Ctrl+C to stop script).")

        try:
            page.pause()
        except:
            pass
        return True

def run_admin_flow(page, config):
    """
    Phase 2: Reconnect -> Login -> Admin Password
    """
    ROUTER_URL = config.get('router_url', "http://192.168.1.1")
    LOGIN_USER = config['login_user']
    LOGIN_PASS = config['login_pass']
    NEW_ADMIN_PASS = config['new_admin_pass']

    print("   🚀 Starting Admin Flow...")

    try:
        # 1. Login
        page.goto(ROUTER_URL)
        page.wait_for_load_state("networkidle")
        if not login_to_router(page, LOGIN_USER, LOGIN_PASS):
             print("   ❌ Login failed in Admin Flow.")
             return False

        # 2. Navigate to Admin
        print("   Step 5: Changing Admin Password...")

        print("   Navigating to 'Advanced'...")
        if page.is_visible("text=Advanced"):
            page.click("text=Advanced")
        elif page.is_visible("#advanced"):
            page.click("#advanced")

        page.wait_for_timeout(1000)

        print("   Navigating to 'System Tools'...")
        if page.is_visible("text=System Tools"):
            page.click("text=System Tools")

        page.wait_for_timeout(1000)

        print("   Navigating to 'Administration'...")
        if page.is_visible("a[url='administration.htm']"):
                page.click("a[url='administration.htm']")
        elif page.is_visible("text=Administration"):
            page.click("text=Administration")

        page.wait_for_timeout(2000)

        # 3. Change Password
        print("   Looking for password fields...")

        if page.is_visible("#oldPwd"):
            page.fill("#oldPwd", LOGIN_PASS)
        elif page.is_visible("input[type='password']"):
            pwds = page.locator("input[type='password']").all()
            if len(pwds) >= 3:
                pwds[0].fill(LOGIN_PASS)
                pwds[1].fill(NEW_ADMIN_PASS)
                pwds[2].fill(NEW_ADMIN_PASS)

        if page.is_visible("#newPwd"):
            page.fill("#newPwd", NEW_ADMIN_PASS)
        if page.is_visible("#cfmPwd"):
            page.fill("#cfmPwd", NEW_ADMIN_PASS)

        # Save Admin
        if page.is_visible("#save"):
            print("   Saving Admin Password...")
            page.click("#save")
        elif page.is_visible("button:has-text('Save')"):
            page.click("button:has-text('Save')")

        print("   ✅ Admin Password Changed.")
        return True

    except Exception as e:
        print(f"   ❌ Admin Password Change Failed: {e}")
        save_debug_artifact(page, "admin_flow_error")
        print("   🛑 PAUSING FOR MANUAL INTERVENTION (Admin Flow)!")
        try:
            page.pause()
        except:
            pass
        return True
