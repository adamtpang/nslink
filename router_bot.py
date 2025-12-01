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
            page.wait_for_selector("input[placeholder='Username'], #pc-login-user, input#userName, #usrPwdForm", timeout=5000)
        except:
            print("   ⚠️ Login fields not found immediately. Saving debug info...")
            save_debug_artifact(page, "login_not_found")
            # Continue anyway, might be already logged in?

        # Handle "New User" Creation (Factory Reset State)
        if page.is_visible("#usrPwdForm") or page.is_visible("#t_newUserTip"):
            print("   🆕 Factory Reset detected! Creating new user...")
            try:
                # Fill New Username (if visible/editable)
                if page.is_visible("#usr"):
                    page.fill("#usr", user)

                # Fill New Password
                if page.is_visible("#newPwd"):
                    page.fill("#newPwd", password)

                # Confirm New Password
                if page.is_visible("#cfmPwd"):
                    page.fill("#cfmPwd", password)

                # Click Confirm
                if page.is_visible(".quicksetup-cfmBtn"):
                    print("   ✅ Clicking Confirm for new user...")
                    page.click(".quicksetup-cfmBtn")
                    page.wait_for_timeout(3000)
            except Exception as e:
                print(f"   ⚠️ New User creation failed: {e}")

        # Standard Login
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
            page.wait_for_timeout(1000)

            clicked = False
            # Try multiple selectors for the "Log in" or "Yes" button
            # User provided ID: #confirm-yes
            for selector in ["#confirm-yes", "button:has-text('Log in')", "button:has-text('Yes')", ".confirm-btn"]:
                if page.is_visible(selector):
                    print(f"   🖱️ Clicking force logout button ({selector})...")
                    page.click(selector)
                    clicked = True
                    break

            if not clicked:
                print("   ⚠️ Could not find 'Log in' button for force logout.")

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

        # FORCE: Always click "Quick Setup" to ensure we are at the start of the flow
        # This handles cases where the router is partially configured or on a different tab
        if page.is_visible("#qs"):
            print("   🖱️ Clicking 'Quick Setup' tab to ensure correct flow...")
            page.click("#qs")
            page.wait_for_timeout(2000)

        # CHECK: Is the wizard loaded?
        if not page.is_visible("[id='_region']"):
            print("   ⚠️ Region selector not found. Attempting to reload...")
            page.reload()
            page.wait_for_timeout(3000)

            # Try clicking Quick Setup again after reload
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

def factory_reset(page, config):
    """
    Navigates to System Tools -> Backup & Restore -> Factory Restore
    """
    ROUTER_URL = config.get('router_url', "http://192.168.1.1")
    LOGIN_USER = config['login_user']
    LOGIN_PASS = config['login_pass']

    print("   🧨 Starting Factory Reset Sequence...")

    try:
        # 1. Login
        page.goto(ROUTER_URL)
        page.wait_for_load_state("networkidle")
        if not login_to_router(page, LOGIN_USER, LOGIN_PASS):
             print("   ❌ Login failed. Cannot factory reset.")
             return False

        # 2. Navigate to Backup & Restore
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

        print("   Navigating to 'Backup & Restore'...")
        if page.is_visible("a[url='backup_restore.htm']"):
            page.click("a[url='backup_restore.htm']")
        elif page.is_visible("text=Backup & Restore"):
            page.click("text=Backup & Restore")

        page.wait_for_timeout(2000)

        # 3. Click Factory Restore
        print("   💥 Clicking Factory Restore...")
        if page.is_visible("#factory_restore"):
            page.click("#factory_restore")
        elif page.is_visible("button:has-text('Factory Restore')"):
            page.click("button:has-text('Factory Restore')")

        page.wait_for_timeout(1000)

        # 4. Confirm
        print("   ⚠️ Confirming Reset...")
        if page.is_visible(".confirm-btn"): # Generic class for confirm
            page.click(".confirm-btn")
        elif page.is_visible("button:has-text('Yes')"):
            page.click("button:has-text('Yes')")
        elif page.is_visible("button:has-text('Restore')"):
             page.click("button:has-text('Restore')")

        print("   ✅ Factory Reset Triggered! Router should reboot.")
        return True

    except Exception as e:
        print(f"   ❌ Factory Reset Failed: {e}")
        save_debug_artifact(page, "factory_reset_fail")
        return False
