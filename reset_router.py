from playwright.sync_api import sync_playwright
import router_bot

# Config for the router you want to reset
config = {
    'router_url': "http://192.168.1.1",
    # If the router was just reset, use 'customer' / 'celcomdigi123'
    # If you already changed it, use 'admin' / 'darktalent2024!' (or whatever you set)
    'login_user': "customer",
    'login_pass': "celcomdigi123"
}

def main():
    print("🧨 Manual Factory Reset Script Initiated...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        success = router_bot.factory_reset(page, config)

        if success:
            print("✅ Reset command sent successfully.")
        else:
            print("❌ Reset failed.")

        browser.close()

if __name__ == "__main__":
    main()
