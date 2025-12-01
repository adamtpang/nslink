import csv
import time
from playwright.sync_api import sync_playwright
import wifi_tools
import router_bot

def load_queue():
    queue_file = 'router_queue.csv'
    queue = []
    try:
        with open(queue_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                queue.append(row)
    except FileNotFoundError:
        print(f"⚠️ Queue file '{queue_file}' not found. Creating an empty one.")
        with open(queue_file, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(['S/N', 'Default SSID', 'Default Pass', 'New SSID']) # Write header
    except Exception as e:
        print(f"❌ Error loading queue: {e}")
    return queue

def run_router_mill():
    print("🏭 NS ROUTER MILL: FACTORY MODE ACTIVATED")
    print("   Scanning for routers in queue... (Ctrl+C to stop)\n")

    completed_sns = set()

    while True:
        queue = load_queue()

        # Calculate Progress
        total_routers = len(queue)
        completed_count = len(completed_sns)
        pending_routers = [r for r in queue if r['S/N'] not in completed_sns]

        print(f"📊 PROGRESS: {completed_count}/{total_routers} Configured ({len(pending_routers)} Pending)")

        # 1. SCAN THE AIRWAVES
        visible_ssids = wifi_tools.get_visible_ssids()

        # CHECK: Are any pending routers ALREADY configured?
        for row in list(pending_routers):
            target_ssid_24 = f"{row['New SSID']} 2.4Ghz"
            target_ssid_5 = f"{row['New SSID']} 5.0Ghz"

            if target_ssid_24 in visible_ssids or target_ssid_5 in visible_ssids:
                print(f"   ✅ Found active Target SSID for {row['S/N']}. Marking as COMPLETED.")
                completed_sns.add(row['S/N'])

        # Re-evaluate pending list after checks
        pending_routers = [r for r in queue if r['S/N'] not in completed_sns]

        if not pending_routers:
            print("   🎉 ALL ROUTERS IN QUEUE ARE CONFIGURED! Nice work.")
            print("   (Scanning for new entries in 10s...)")
            time.sleep(10)
            continue

        target_found = None
        print(f"📡 Scanning for defaults... ({len(visible_ssids)} networks found)")

        for row in pending_routers:
            base_ssid = row['Default SSID'].replace("_2.4Ghz", "").replace("_5Ghz", "")

            ssid_24 = f"{base_ssid}_2.4Ghz"
            ssid_5 = f"{base_ssid}_5Ghz"

            if ssid_24 in visible_ssids:
                print(f"   🎯 MATCH! Found {ssid_24} (Target: {row['S/N']})")
                target_found = row
                target_found['Connect SSID'] = ssid_24
                break

            if ssid_5 in visible_ssids:
                print(f"   🎯 MATCH! Found {ssid_5} (Target: {row['S/N']})")
                target_found = row
                target_found['Connect SSID'] = ssid_5
                break

        if not target_found:
            if len(visible_ssids) > 0:
                print(f"   ⚠️ No match found. Visible: {visible_ssids}")
            time.sleep(3)
            continue

        # 2. PROCESS THE FOUND ROUTER
        row = target_found
        print(f"\n==========================================")
        print(f"🛠️  PROCESSING: {row['S/N']}")
        print(f"    Connect: {row['Connect SSID']}")
        print(f"    Target:  {row['New SSID']}")
        print(f"==========================================")

        # --- PHASE 1: INITIAL SETUP (WIZARD) ---
        print(f"1️⃣  [PHASE 1] Connecting to {row['Connect SSID']}...")
        connected = wifi_tools.connect_to_wifi(row['Connect SSID'], row['Default Pass'])

        if not connected:
            print("❌ Connection failed. Retrying scan...")
            continue

        print("2️⃣  [PHASE 1] Running Factory Reset Wizard...")
        config = {
            'router_url': "http://192.168.1.1",
            'login_user': "customer",
            'login_pass': "celcomdigi123",
            'new_ssid': row['New SSID'],
            'new_wifi_pass': "darktalent2024!",
            'new_admin_pass': "darktalent2024!"
        }

        success_p1 = False
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=False)
                context = browser.new_context()
                page = context.new_page()
                success_p1 = router_bot.run_wizard_flow(page, config)
                browser.close()
        except Exception as e:
            print(f"❌ Playwright Error: {e}")

        if not success_p1:
            print("❌ Phase 1 Failed. Aborting this router.")
            continue

        # --- INTERMISSION: RECONNECT ---
        print("\n🔄 Router is rebooting. Waiting for new SSID to appear...")

        # Smart Wait: Poll for the new SSID instead of hard sleep
        new_ssid_24 = f"{row['New SSID']} 2.4Ghz"
        new_pass = "darktalent2024!"

        ssid_detected = False
        for i in range(15): # Try for up to 75 seconds (15 * 5s)
            visible = wifi_tools.get_visible_ssids()
            if new_ssid_24 in visible:
                print(f"   ✨ New SSID '{new_ssid_24}' detected! Proceeding...")
                ssid_detected = True
                break
            print(f"   ⏳ Waiting for {new_ssid_24}... ({i+1}/15)")
            time.sleep(5)

        if not ssid_detected:
            print("   ⚠️ New SSID not found after reboot. Trying to connect anyway...")

        print(f"3️⃣  [PHASE 2] Connecting to New WiFi: {new_ssid_24}...")
        reconnected = False
        for _ in range(3):
            if wifi_tools.connect_to_wifi(new_ssid_24, new_pass):
                reconnected = True
                break
            print("   Retrying connection...")
            time.sleep(5)

        if not reconnected:
            print("❌ Failed to reconnect. Admin Config skipped.")
            continue

        # --- PHASE 2: ADMIN CONFIG ---
        print("4️⃣  [PHASE 2] Configuring Admin Password...")
        success_p2 = False
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=False)
                context = browser.new_context()
                page = context.new_page()
                success_p2 = router_bot.run_admin_flow(page, config)
                browser.close()
        except Exception as e:
            print(f"❌ Playwright Error: {e}")

        if success_p2:
            print(f"✅ Router {row['S/N']} FULLY CONFIGURED!")
            completed_sns.add(row['S/N'])
        else:
            print(f"⚠️ Router {row['S/N']} Partial Config (WiFi OK, Admin Failed).")

        print("------------------------------------------")
        print("Resuming Scan in 5s...")
        time.sleep(5)

if __name__ == "__main__":
    run_router_mill()