import csv
import time
from playwright.sync_api import sync_playwright
import wifi_tools  # Your new module
import router_bot  # Your refactored logic

def run_router_mill():
    # 1. Load the Queue
    queue_file = 'router_queue.csv'
    # EXPECTED CSV HEADERS: Location ID, S/N, SIM ID, Default SSID, Default Pass, New SSID

    print(f"📂 Loading {queue_file}...")
    with open(queue_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        queue = list(reader)

    print(f"🔥 Loaded {len(queue)} routers to configure.\n")

    for index, row in enumerate(queue):
        print(f"==========================================")
        print(f"🛠️  PROCESSING ROUTER {index + 1}/{len(queue)}")
        print(f"    Target: {row['S/N']} -> {row['New SSID']}")
        print(f"==========================================")

        # A. CONNECT TO ROUTER (The OS Hand)
        # You need to ensure your CSV has 'Default SSID' and 'Default Pass'
        # If not, you might calculate it or prompt user.
        default_ssid = row.get('Default SSID')
        default_pass = row.get('Default Pass') # Or calculate from S/N?

        if not default_ssid:
            print("❌ MISSING DATA: No Default SSID in CSV.")
            continue

        print(f"1️⃣  Switching WiFi to {default_ssid}...")
        connected = wifi_tools.connect_to_wifi(default_ssid, default_pass)

        if not connected:
            print("❌ Failed to connect to router. Is it plugged in and reset?")
            response = input("   (r)etry or (s)kip? ")
            if response.lower() == 's': continue
            # Retry logic could go here
            continue

        # B. CONFIGURE ROUTER (The Browser Eye)
        print("2️⃣  Launching Browser Configuration...")

        # Prepare the config object
        config = {
            'router_url': "http://192.168.1.1", # Or 0.1, depends on model
            'login_user': "customer", # Or from CSV
            'login_pass': "celcomdigi123", # Or from CSV
            'new_ssid': row['New SSID'],
            'new_wifi_pass': "darktalent2024!",
            'new_admin_pass': "darktalent2024!"
        }

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context()
            page = context.new_page()

            success = router_bot.configure_router_logic(page, config)

            browser.close()

        if success:
            print(f"✅ Router {row['S/N']} Configured Successfully!")
            # Optional: Write status back to CSV or a log file
        else:
            print(f"❌ Failed to configure {row['S/N']}")

        print("------------------------------------------")
        print("Waiting 10s before next router (swap time)...")
        time.sleep(10)

if __name__ == "__main__":
    run_router_mill()