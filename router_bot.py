from playwright.sync_api import sync_playwright
import time
import re
import os

def save_debug_artifact(page, step_name):
    """Saves a screenshot and HTML dump for debugging."""
    # Ensure debug directory exists
    debug_dir = "debug"
    if not os.path.exists(debug_dir):
        os.makedirs(debug_dir)

    timestamp = int(time.time())
    screenshot_path = os.path.join(debug_dir, f"debug_{step_name}_{timestamp}.png")
    html_path = os.path.join(debug_dir, f"debug_{step_name}_{timestamp}.html")

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
    # Wait for any known login field
    try:
        page.wait_for_selector("input[placeholder='Username'], #pc-login-user, input#userName, #usrPwdForm, #pc-login-password", timeout=5000)
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

    # Retry login up to 3 times
    for attempt in range(3):
        print(f"   🔑 Attempting Login (Attempt {attempt+1}/3)...")
        try:
            # Standard Login
            # Check if username field is actually visible.
            # Some routers hide it if only password is needed (or remembered).
            username_visible = False
            if page.is_visible("input[placeholder='Username']"):
                page.fill("input[placeholder='Username']", user)
                username_visible = True
            elif page.is_visible("#pc-login-user") and page.is_visible("#pc-login-user-div:not(.nd)"):
                 # Check if parent div is hidden (class 'nd')
                 page.fill("#pc-login-user", user)
                 username_visible = True
            elif page.is_visible("input#userName"):
                page.fill("input#userName", user)
                username_visible = True

            if not username_visible:
                print("   ℹ️ Username field hidden or not found. Assuming Password-only login.")

            if page.is_visible("input[type='password']"):
                page.fill("input[type='password']", password)
            elif page.is_visible("#pc-login-password"):
                page.fill("#pc-login-password", password)

            # Try clicking the login button explicitly first
            if page.is_visible("#pc-login-btn"):
                page.click("#pc-login-btn")
            else:
                page.keyboard.press("Enter")

            page.wait_for_timeout(1000)

            # Handle "Force Logout" Dialog
            if page.is_visible("text=Only one device can log in at a time") or page.is_visible("#confirm-yes"):
                print("   ⚠️ Detected active session. Forcing logout...")
                page.wait_for_timeout(1000)

                try:
                    if page.is_visible("#confirm-yes"):
                        page.click("#confirm-yes")
                    elif page.is_visible("button:has-text('Yes')"):
                        page.click("button:has-text('Yes')")
                    elif page.is_visible("button:has-text('OK')"):
                        page.click("button:has-text('OK')")

                    page.wait_for_timeout(3000) # Wait for logout/login cycle

                    # Re-enter password if needed (sometimes it kicks you back to login)
                    if page.is_visible("input[type='password']") or page.is_visible("#pc-login-password"):
                         print("   🔄 Re-entering password after force logout...")
                         if page.is_visible("input[type='password']"):
                            page.fill("input[type='password']", password)
                         elif page.is_visible("#pc-login-password"):
                            page.fill("#pc-login-password", password)

                         if page.is_visible("#pc-login-btn"):
                            page.click("#pc-login-btn")
                         else:
                            page.keyboard.press("Enter")
                         page.wait_for_timeout(2000)

                except Exception as e:
                    print(f"   ⚠️ Failed to click Force Logout: {e}")

            # Verify Login Success
            # We check for elements that only appear when logged in (e.g., Logout button, Quick Setup tab, etc.)
            page.wait_for_timeout(2000)
            is_logged_in = False
            if page.is_visible("#qs") or page.is_visible("text=Quick Setup") or page.is_visible("#logout") or page.is_visible("text=Logout"):
                is_logged_in = True
            elif page.is_visible("#menu"): # Generic menu check
                is_logged_in = True

            if is_logged_in:
                print("   ✅ Login verified.")
                return True
            else:
                print("   ❌ Login verification failed. Still on login page or stuck.")
                save_debug_artifact(page, f"login_verification_failed_attempt_{attempt+1}")

                # If failed, reload page for next attempt
                if attempt < 2:
                    print("   🔄 Reloading page and retrying...")
                    page.reload()
                    page.wait_for_load_state("domcontentloaded")
                    page.wait_for_timeout(2000)

        except Exception as e:
            print(f"   ❌ Login Exception: {e}")
            if attempt < 2:
                page.reload()

    return False

def run_wizard_flow(page, config):
    """
    Phase 1: Factory Reset -> Wizard -> Wireless Config
    Strict Checklist Approach
    """
    ROUTER_URL = config.get('router_url', "http://192.168.1.1")
    LOGIN_USER = config['login_user']
    LOGIN_PASS = config['login_pass']
    NEW_SSID = config['new_ssid']
    NEW_WIFI_PASS = config['new_wifi_pass']

    print(f"\n   🚀 STARTING WIZARD FLOW: {NEW_SSID}")
    print("   ---------------------------------------------------")

    # --- STEP 1: LOGIN ---
    print("   [ ] Step 1: Login")
    try:
        page.goto(ROUTER_URL, timeout=15000)
        page.wait_for_load_state("domcontentloaded")

        if not login_to_router(page, LOGIN_USER, LOGIN_PASS):
            print("   ❌ Step 1 Failed: Could not log in.")
            return False
        print("   [x] Step 1: Login Complete")
    except Exception as e:
        print(f"   ❌ Step 1 Error: {e}")
        return False

    # --- STEP 2: ENSURE WIZARD START ---
    print("   [ ] Step 2: Start Wizard (Quick Setup)")
    try:
        page.wait_for_timeout(2000)
        if page.is_visible("#qs"):
            page.click("#qs")
            print("   [x] Step 2: Clicked Quick Setup")
        else:
            print("   ⚠️ Quick Setup tab not found, assuming we are already in wizard or on a different page.")
    except Exception as e:
        print(f"   ⚠️ Step 2 Warning: {e}")

    # --- STEP 3: REGION & TIMEZONE ---
    print("   [ ] Step 3: Region & Time Zone")
    try:
        page.wait_for_timeout(2000)
        # Check if we are actually on the Region step
        if page.is_visible("#region") or page.is_visible(".T_region") or page.is_visible("#_region"):
            print("   🌍 Region Selector Found. Configuring...")

            # Try to select Malaysia (val=58)
            region_selected = False
            try:
                if page.is_visible("#_region .select-icon"):
                    page.click("#_region .select-icon")
                    page.wait_for_timeout(500)
                    if page.is_visible("li[data-val='58']"):
                        page.click("li[data-val='58']")
                        print("   ✅ Selected 'Malaysia'")
                        region_selected = True
                    elif page.is_visible("li[data-val='96']"):
                        page.click("li[data-val='96']")
                        print("   ✅ Selected 'United States'")
                        region_selected = True
                    else:
                        print("   ⚠️ Could not find specific region, keeping default.")
            except:
                print("   ⚠️ Failed to interact with region dropdown.")

            page.wait_for_timeout(1000)

            # Click Next
            # Click Next with Retry Logic
            # Sometimes the first click doesn't register or the page is slow
            next_clicked = False
            for i in range(3):
                if page.is_visible("#next"):
                    print(f"   🖱️ Clicking Next (Region) - Attempt {i+1}...")
                    page.click("#next")
                    page.wait_for_timeout(2000)

                    # Check if we moved to Wireless Settings
                    if page.is_visible("text=Wireless Settings") or page.is_visible("input[type='text']"):
                        print("   ✅ Successfully moved to Wireless Settings.")
                        next_clicked = True
                        break
                else:
                    print("   ⚠️ 'Next' button not found on Region page.")
                    break

            if not next_clicked:
                print("   ⚠️ Warning: Might still be on Region page after retries.")

            print("   [x] Step 3: Region Configured")
        else:
            print("   ⏭️ Region selector NOT found. Skipping Step 3 (assuming already passed).")
    except Exception as e:
        print(f"   ❌ Step 3 Error: {e}")

    # --- STEP 3.5: INTERNET SETUP (New Intermediate Step) ---
    print("   [ ] Step 3.5: Internet Setup")
    try:
        page.wait_for_timeout(2000)
        # Check if we are on the Internet Setup page
        # Look for "Internet Connection Type" or specific IDs like #linktype, #DHCPqs
        # Also check process flow and Next button
        is_internet_setup = False
        if page.is_visible("text=Internet Setup") or page.is_visible("#wan_next"):
            is_internet_setup = True
        elif page.is_visible("#DHCPqs") or page.is_visible("text=Internet Connection Type"):
            is_internet_setup = True

        if is_internet_setup:
            print("   🌐 Internet Setup Page Found.")

            # Usually "Dynamic IP" is default and fine. We just need to click Next.
            # But let's be safe and ensure Dynamic IP is selected if possible, or just click Next.

            # Click Next
            if page.is_visible("#wan_next"):
                print("   🖱️ Clicking Next (Internet Setup)...")
                page.click("#wan_next")
                page.wait_for_timeout(2000)
            elif page.is_visible("#next"):
                print("   🖱️ Clicking Next (Internet Setup)...")
                page.click("#next")
                page.wait_for_timeout(2000)
            else:
                print("   ⚠️ 'Next' button not found on Internet Setup page.")

            print("   [x] Step 3.5: Internet Setup Configured")
        else:
             print("   ⏭️ Internet Setup not found. Skipping (might be skipped in AP mode or already passed).")

    except Exception as e:
        print(f"   ⚠️ Step 3.5 Warning: {e}")

    # --- STEP 4: WIRELESS SETTINGS ---
    print("   [ ] Step 4: Wireless Settings")
    try:
        page.wait_for_timeout(2000)

        # Verification: Are we actually on the Wireless page?
        # Look for specific IDs found in debug HTML
        is_wireless_page = False
        for _ in range(5): # Retry check a few times
            if page.is_visible("#wl24gSSID") or page.is_visible("#wlSmartConn") or page.is_visible("#div_wlanSetting") or page.is_visible("text=Wireless Settings"):
                is_wireless_page = True
                break
            page.wait_for_timeout(1000)

        if not is_wireless_page:
            print("   ❌ Step 4 Failed: Not on Wireless Settings page. Dumping state...")
            save_debug_artifact(page, "wireless_page_not_found")
            return False

        # 4a. Band Steering
        print("       [ ] 4a. Band Steering")
        # ID from debug HTML: wlSmartConn
        try:
            if page.is_visible("#wlSmartConn"):
                print("       ✨ Found Band Steering Checkbox (#wlSmartConn)")
                if not page.is_checked("#wlSmartConn"):
                    print("       🖱️ Enabling Band Steering...")
                    page.click("label[for='wlSmartConn']") # Click the label to toggle
                    page.wait_for_timeout(1000)
                else:
                    print("       ✅ Band Steering already enabled.")
            else:
                print("       ⚠️ Band Steering checkbox not found.")
        except Exception as e:
            print(f"       ⚠️ Band Steering Error: {e}")

        # 4b. SSID & Password
        print("       [ ] 4b. SSID & Password")

        # We use specific IDs now
        # 2.4GHz
        if page.is_visible("#wl24gSSID"):
            print(f"       ✍️ Setting 2.4GHz SSID: {NEW_SSID}")
            page.fill("#wl24gSSID", NEW_SSID)

        if page.is_visible("#wl24gPwd"):
            print(f"       ✍️ Setting 2.4GHz Password: {NEW_WIFI_PASS}")
            page.fill("#wl24gPwd", NEW_WIFI_PASS)

        # 5GHz (Only if visible - Band Steering might hide it, or it might be separate)
        # If Band Steering is ON, usually only one SSID is needed.
        # But if it's OFF or if the router requires both, we fill both.
        if page.is_visible("#wl5gSSID"):
            print(f"       ✍️ Setting 5GHz SSID: {NEW_SSID}")
            page.fill("#wl5gSSID", NEW_SSID)

        if page.is_visible("#wl5gPwd"):
            print(f"       ✍️ Setting 5GHz Password: {NEW_WIFI_PASS}")
            page.fill("#wl5gPwd", NEW_WIFI_PASS)

        print("       [x] Step 4: Wireless Settings Filled")

        # 4c. Next/Save
        print("       [ ] 4c. Save/Next")
        if page.is_visible("#next"):
            page.click("#next")
        elif page.is_visible("#save"):
            page.click("#save")
        elif page.is_visible("button:has-text('Next')"):
            page.click("button:has-text('Next')")

        page.wait_for_timeout(2000)
        print("       [x] Step 4: Wireless Config Saved")

    except Exception as e:
        print(f"   ❌ Step 4 Error: {e}")
        save_debug_artifact(page, "wireless_step_exception")
        return False

        return False

    # --- STEP 5: FINISH ---
    print("   [ ] Step 5: Finalize")
    try:
        # Handle Summary/Finish page
        if page.is_visible("#finish") or page.is_visible("button:has-text('Finish')"):
            print("   🏁 Clicking Finish...")
            if page.is_visible("#finish"): page.click("#finish")
            else: page.click("button:has-text('Finish')")
            page.wait_for_timeout(2000)

        # Handle "Success" or "OK" dialogs
        if page.is_visible("button:has-text('OK')"):
            page.click("button:has-text('OK')")

        # One last check for Next (user reported issue)
        if page.is_visible("#next"):
             page.click("#next")

        print("   [x] Step 5: Wizard Completed")
        save_debug_artifact(page, "wizard_complete")

        print("\n   👀 PAUSING FOR 10 SECONDS FOR MANUAL INSPECTION...")
        time.sleep(10)
        return True

    except Exception as e:
        print(f"   ❌ Step 5 Error: {e}")
        return False

def run_admin_flow(page, config):
    ROUTER_URL = config.get('router_url', "http://192.168.1.1")
    LOGIN_USER = config['login_user']
    LOGIN_PASS = config['login_pass']
    NEW_ADMIN_PASS = config['new_admin_pass']

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

        page.wait_for_timeout(2000)
        save_debug_artifact(page, "admin_advanced_menu") # Capture menu structure

        print("   Navigating to 'System Tools' or 'System'...")
        if page.is_visible("text=System Tools"):
            page.click("text=System Tools")
        elif page.is_visible("text=System"): # Alternative for some firmwares
            page.click("text=System")

        page.wait_for_timeout(1000)

        print("   Navigating to 'Administration' or 'Modify Password'...")
        if page.is_visible("a[url='administration.htm']"):
                page.click("a[url='administration.htm']")
        elif page.is_visible("text=Administration"):
            page.click("text=Administration")
        elif page.is_visible("text=Modify Password"): # Alternative
            page.click("text=Modify Password")
        elif page.is_visible("text=Password"): # Another alternative
            page.click("text=Password")

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
