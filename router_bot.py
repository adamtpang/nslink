from playwright.sync_api import sync_playwright
import time

def configure_router_logic(page, config):
    """
    The core logic.
    Accepts a 'page' object and a 'config' dict:
    {
        'router_url': '...',
        'login_user': '...',
        'login_pass': '...',
        'new_ssid': '...',
        'new_wifi_pass': '...',
        'new_admin_pass': '...'
    }
    """

    ROUTER_URL = config.get('router_url', "http://192.168.1.1")
    LOGIN_USER = config['login_user']
    LOGIN_PASS = config['login_pass']
    NEW_SSID = config['new_ssid']
    NEW_WIFI_PASS = config['new_wifi_pass']
    NEW_ADMIN_PASS = config['new_admin_pass']

    print(f"   🚀 Starting Playwright Sequence for {NEW_SSID}...")

    # 1. BREACH THE GATE (Login)
    print("   Step 1: Login...")
    page.goto(ROUTER_URL)
    # page.wait_for_load_state("networkidle") # Sometimes risky on cheap routers, simple wait is better
    page.wait_for_timeout(2000)

    try:
        # Flexible Login Selectors
        if page.is_visible("#pc-login-user"):
            page.fill("#pc-login-user", LOGIN_USER)
        elif page.is_visible("input#userName"):
            page.fill("input#userName", LOGIN_USER)

        if page.is_visible("#pc-login-password"):
            page.fill("#pc-login-password", LOGIN_PASS)
        elif page.is_visible("input[type='password']"):
            page.fill("input[type='password']", LOGIN_PASS)

        page.keyboard.press("Enter")
        page.wait_for_timeout(3000)
    except Exception as e:
        print(f"   ⚠️ Login Hiccup: {e}")

    # 2. NAVIGATE TO WIRELESS
    print("   Step 2: Navigating to Wireless...")
    try:
        if page.is_visible("a[url='wirelessBasic.htm']"):
            page.click("a[url='wirelessBasic.htm']")
        elif page.is_visible("text=Wireless"):
            page.click("text=Wireless")
        page.wait_for_timeout(2000)
    except Exception as e:
         print(f"   ❌ Navigation Failed: {e}")
         return False

    # 3. SET SSID (The main event)
    print(f"   Step 3: Setting SSID to '{NEW_SSID}'...")

    # Enable Bands logic here (Keep your original code snippets if needed)
    # ... [Your Band Enable Logic from original script goes here if crucial] ...

    # Set SSID
    target_ssid_selector = "#ssid_2g"
    if not page.is_visible(target_ssid_selector):
        if page.is_visible("#ssid"): target_ssid_selector = "#ssid"

    if page.is_visible(target_ssid_selector):
        page.fill(target_ssid_selector, "")
        page.fill(target_ssid_selector, NEW_SSID)
    else:
        print("   ❌ Could not find SSID field!")
        return False

    # Set WiFi Password
    target_pwd_selector = "#wpa2PersonalPwd_2g"
    if not page.is_visible(target_pwd_selector):
         if page.is_visible("#wpa2PersonalPwd"): target_pwd_selector = "#wpa2PersonalPwd"

    if page.is_visible(target_pwd_selector):
        page.fill(target_pwd_selector, "")
        page.fill(target_pwd_selector, NEW_WIFI_PASS)

    # Save
    if page.is_visible("#save_2g"):
        page.click("#save_2g")
    elif page.is_visible("#save"):
        page.click("#save")

    print("   ✅ Wireless Settings Saved. Router may reboot.")
    page.wait_for_timeout(5000)

    return True
