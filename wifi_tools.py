import subprocess
import time
import os
import binascii

def create_wifi_profile_xml(ssid, password):
    """Generates the XML needed for Windows to recognize a WPA2 network."""
    ssid_hex = binascii.hexlify(ssid.encode()).decode()

    profile_xml = f"""<?xml version="1.0"?>
<WLANProfile xmlns="http://www.microsoft.com/networking/WLAN/profile/v1">
    <name>{ssid}</name>
    <SSIDConfig>
        <SSID>
            <hex>{ssid_hex}</hex>
            <name>{ssid}</name>
        </SSID>
    </SSIDConfig>
    <connectionType>ESS</connectionType>
    <connectionMode>auto</connectionMode>
    <MSM>
        <security>
            <authEncryption>
                <authentication>WPA2PSK</authentication>
                <encryption>AES</encryption>
                <useOneX>false</useOneX>
            </authEncryption>
            <sharedKey>
                <keyType>passPhrase</keyType>
                <protected>false</protected>
                <keyMaterial>{password}</keyMaterial>
            </sharedKey>
        </security>
    </MSM>
</WLANProfile>"""
    return profile_xml

def get_visible_ssids():
    """
    Returns a list of all visible SSIDs currently broadcasting.
    Parses 'netsh wlan show networks'.
    """
    try:
        # mode=bssid forces a fresher scan
        result = subprocess.run(["netsh", "wlan", "show", "networks", "mode=bssid"], capture_output=True, text=True)

        ssids = []
        for line in result.stdout.split('\n'):
            line = line.strip()
            if line.startswith("SSID"):
                # Format: "SSID 1 : NetworkName"
                parts = line.split(":", 1)
                if len(parts) > 1:
                    ssid = parts[1].strip()
                    if ssid: # Ignore empty SSIDs
                        ssids.append(ssid)

        # DEBUG: If we see very few networks, dump the raw output to understand why
        if len(ssids) < 2:
            print("\n   ⚠️ DEBUG: Low network count detected. Raw netsh output:")
            print(result.stdout[:500]) # Print first 500 chars
            print("   ⚠️ End of raw output.\n")

        return ssids
    except Exception as e:
        print(f"   ⚠️ Error scanning networks: {e}")
        return []

def connect_to_wifi(ssid, password):
    print(f"📡 OS COMMAND: Connecting to '{ssid}'...")

    # 1. Create the XML Profile
    safe_ssid = ssid.replace(" ", "_")
    filename = f"temp_wifi_{safe_ssid}.xml"
    abs_filename = os.path.abspath(filename)

    xml_content = create_wifi_profile_xml(ssid, password)

    with open(abs_filename, "w") as f:
        f.write(xml_content)

    try:
        # 2. Add Profile to Windows
        add_cmd = ["netsh", "wlan", "add", "profile", f"filename={abs_filename}"]
        subprocess.run(add_cmd, capture_output=True, text=True, check=True)

        # 3. Connect
        connect_cmd = ["netsh", "wlan", "connect", f"name={ssid}"]
        result = subprocess.run(connect_cmd, capture_output=True, text=True, check=True)

        # 4. Wait for connection verification
        print("   ⏳ Waiting for IP address...")
        for _ in range(15):
            result = subprocess.run(["netsh", "wlan", "show", "interfaces"], capture_output=True, text=True)
            if f"SSID                   : {ssid}" in result.stdout:
                print(f"   ✅ Connected to {ssid}")
                return True
            time.sleep(1)

        print("   ❌ Connection timed out.")
        return False

    except subprocess.CalledProcessError as e:
        print(f"   ❌ Command Failed: {e.cmd}")
        return False
    except Exception as e:
        print(f"   ❌ General Error: {e}")
        return False
    finally:
        if os.path.exists(abs_filename):
            os.remove(abs_filename)

def get_current_wifi_ssid():
    result = subprocess.run(["netsh", "wlan", "show", "interfaces"], capture_output=True, text=True)
    for line in result.stdout.split('\n'):
        if "SSID" in line and "BSSID" not in line:
            return line.split(":")[1].strip()
    return None