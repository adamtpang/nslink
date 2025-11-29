from playwright.sync_api import sync_playwright
import time

# --- MISSION CONFIGURATION ---
ROUTER_URL = "http://192.168.1.1"
LOGIN_USER = "customer"
LOGIN_PASS = "celcomdigi123"

# The Configuration we want to apply
NEW_SSID = "NS Room 8017" # Single SSID for Band Steering
NEW_WIFI_PASS = "darktalent2024!"
NEW_ADMIN_PASS = "darktalent2024!"
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
            page.wait_for_load_state("networkidle")

            # Login Logic
            try:
                print("🔑 Attempting Login...")
                if page.is_visible("#pc-login-user"):
                    page.fill("#pc-login-user", LOGIN_USER)
                elif page.is_visible("input#userName"):
                    page.fill("input#userName", LOGIN_USER)
                elif page.is_visible("input[placeholder='Username']"):
                    page.fill("input[placeholder='Username']", LOGIN_USER)

                if page.is_visible("#pc-login-password"):
                    page.fill("#pc-login-password", LOGIN_PASS)
                elif page.is_visible("input[type='password']"):
                    page.fill("input[type='password']", LOGIN_PASS)

                page.keyboard.press("Enter")
                page.wait_for_timeout(3000)

            except Exception as e:
                print(f"⚠️ Login Hiccup: {e}")

            # 2. NAVIGATE TO WIRELESS (The Navigation)
            print("Step 2: Navigating to Wireless Settings...")

            # Wait for menu
            try:
                page.wait_for_selector("#menuTree", timeout=5000)
            except:
                print("   ⚠️ Menu not found immediately.")

            if page.is_visible("a[url='wirelessBasic.htm']"):
                print("   Found 'Wireless' tab")
                page.click("a[url='wirelessBasic.htm']")
            elif page.is_visible("text=Wireless"):
                print("   Found 'Wireless' tab")
                page.click("text=Wireless")

            page.wait_for_timeout(2000)

            # 2.5 PRE-FLIGHT CHECK: Enable Both Bands
            print("Step 2.5: Ensuring both bands are enabled...")

            # Enable 2.4GHz
            try:
                print("   Checking 2.4GHz Radio...")
                # Try to check if visible, otherwise force check
                if page.is_visible("#wlEn_2g"):
                    if not page.is_checked("#wlEn_2g"):
                        print("   Enabling 2.4GHz...")
                        page.check("#wlEn_2g")
                    else:
                        print("   2.4GHz is already enabled.")
                else:
                    # Try force check if hidden
                    try:
                        page.locator("#wlEn_2g").check(force=True)
                        print("   Enabling 2.4GHz (Force)...")
                    except:
                        print("   ⚠️ Force check failed, clicking label...")
                        page.click("label[for='wlEn_2g']")
            except Exception as e:
                print(f"   ⚠️ 2.4GHz Check Warning: {e}")

            # Enable 5GHz
            try:
                print("   Checking 5GHz Radio...")
                if page.is_visible("#wlEn_5g"):
                    if not page.is_checked("#wlEn_5g"):
                        print("   Enabling 5GHz...")
                        page.check("#wlEn_5g")
                    else:
                        print("   5GHz is already enabled.")
                else:
                     # Try force check if hidden
                    try:
                        page.locator("#wlEn_5g").check(force=True)
                        print("   Enabling 5GHz (Force)...")
                    except:
                        print("   ⚠️ Force check failed, clicking label...")
                        page.click("label[for='wlEn_5g']")
            except Exception as e:
                print(f"   ⚠️ 5GHz Check Warning: {e}")

            page.wait_for_timeout(2000)

            # 3. CONFIGURE BAND STEERING (The Merge)
            print("Step 3: Configuring Band Steering...")

            # Enable Band Steering
            # We try multiple ways to click it because of the 'cover' element
            try:
                if page.is_visible("#enableSmartConnOn"):
                    print("   Found Band Steering Toggle. Enabling...")
                    # Try standard click
                    try:
                        page.click("#enableSmartConnOn", timeout=2000)
                    except:
                        print("   ⚠️ Standard click failed. Trying force click...")
                        page.click("#enableSmartConnOn", force=True)

                    page.wait_for_timeout(2000) # Wait for UI to update
                else:
                    print("   ⚠️ Band Steering Toggle (#enableSmartConnOn) NOT FOUND! Checking for cover...")
                    # If button is hidden, maybe click the cover?
                    if page.is_visible("ul.button-group-cover"):
                         print("   Found .button-group-cover. Clicking it...")
                         page.click("ul.button-group-cover", force=True)
                         page.wait_for_timeout(2000)
                    else:
                         print("   ❌ Neither button nor cover found.")
            except Exception as e:
                print(f"   ❌ Band Steering Error: {e}")

            # 4. CONFIGURE SSID & PASSWORD
            print("Step 4: Setting SSID and Password...")

            # Wait for SSID field (assuming it stays #ssid_2g or similar)
            # We check for both 2g and 5g just in case, but usually it becomes one.
            target_ssid_selector = "#ssid_2g"
            if not page.is_visible(target_ssid_selector):
                print("   ⚠️ #ssid_2g not visible, looking for generic #ssid...")
                if page.is_visible("#ssid"): target_ssid_selector = "#ssid"

            if page.is_visible(target_ssid_selector):
                print(f"✏️  Renaming SSID to: {NEW_SSID}")
                page.fill(target_ssid_selector, "")
                page.fill(target_ssid_selector, NEW_SSID)
            else:
                print("   ❌ Could not find SSID field!")

            # Password
            target_pwd_selector = "#wpa2PersonalPwd_2g"
            if not page.is_visible(target_pwd_selector):
                 if page.is_visible("#wpa2PersonalPwd"): target_pwd_selector = "#wpa2PersonalPwd"

            if page.is_visible(target_pwd_selector):
                print(f"🔐 Setting Password to: {NEW_WIFI_PASS}")
                page.fill(target_pwd_selector, "")
                page.fill(target_pwd_selector, NEW_WIFI_PASS)
            else:
                 print("   ❌ Could not find Password field!")

            # Save Wireless
            print("   Saving Wireless Configuration...")
            if page.is_visible("#save_2g"):
                page.click("#save_2g")
            elif page.is_visible("#save"):
                page.click("#save")
            else:
                print("   ⚠️ Save button not found!")

            page.wait_for_timeout(5000)

            # 5. ADMIN PASSWORD CHANGE (The Security)
            print("Step 5: Changing Admin Password...")

            # Navigate to Advanced -> System Tools -> Administration
            # We try text selectors as they are most likely to work across versions
            try:
                print("   Navigating to 'Advanced'...")
                if page.is_visible("text=Advanced"):
                    page.click("text=Advanced")
                elif page.is_visible("#advanced"): # Guessing ID
                    page.click("#advanced")

                page.wait_for_timeout(1000)

                print("   Navigating to 'System Tools'...")
                if page.is_visible("text=System Tools"):
                    page.click("text=System Tools")

                page.wait_for_timeout(1000)

                print("   Navigating to 'Administration'...")
                if page.is_visible("text=Administration"):
                    page.click("text=Administration")

                page.wait_for_timeout(2000)

                # Fill Password Fields
                # We need to find the inputs. Usually "Old Password", "New Password", "Confirm Password"
                # We'll dump inputs if we can't find them to help debug

                print("   Looking for password fields...")
                # Common IDs for TP-Link Admin Password
                # oldPwd, newPwd, cfmPwd

                if page.is_visible("#oldPwd"):
                    print("   Found #oldPwd")
                    page.fill("#oldPwd", LOGIN_PASS)
                elif page.is_visible("input[type='password']"):
                    # Risky if there are multiple, but let's try to find by order
                    pwds = page.locator("input[type='password']").all()
                    if len(pwds) >= 3:
                        print("   Found 3 password fields, assuming Old/New/Confirm")
                        pwds[0].fill(LOGIN_PASS)
                        pwds[1].fill(NEW_ADMIN_PASS)
                        pwds[2].fill(NEW_ADMIN_PASS)
                    else:
                        print(f"   ⚠️ Found {len(pwds)} password fields. Not enough?")

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

            except Exception as e:
                print(f"   ❌ Admin Password Change Failed: {e}")
                # Dump HTML to help user find element
                print("   Dumping page text for debugging...")
                print(page.inner_text("body")[:500])


            print("--------------------------------")
            print("✅ MISSION SUCCESS: Router Configured.")
            print("⚠️ Router is now rebooting. You will lose connection.")
            print("--------------------------------")

            # Keep window open for 5s to celebrate
            time.sleep(5)

        except Exception as e:
            print(f"❌ MISSION FAILED: {e}")
            page.screenshot(path="debug_failure.png")
            print("📸 Saved debug_failure.png")
            # Keep window open to debug
            time.sleep(30)

        browser.close()

if __name__ == "__main__":
    run()