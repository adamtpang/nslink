import subprocess
import time
import os
import binascii

def create_wifi_profile_xml(ssid, password):
    """Generates the XML needed for Windows to recognize a WPA2 network."""
    # Windows needs the SSID in Hex format for the profile
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

def connect_to_wifi(ssid, password):
    print(f"📡 OS COMMAND: Connecting to '{ssid}'...")

    # 1. Create the XML Profile
    xml_content = create_wifi_profile_xml(ssid, password)
    filename = f"temp_wifi_{ssid}.xml"

    with open(filename, "w") as f:
        f.write(xml_content)

    try:
        # 2. Add Profile to Windows
        # netsh wlan add profile filename="temp_wifi_XYZ.xml"
        add_cmd = ["netsh", "wlan", "add", "profile", f"filename={filename}"]
        subprocess.run(add_cmd, capture_output=True, check=True)

        # 3. Connect
        # netsh wlan connect name="SSID"
        connect_cmd = ["netsh", "wlan", "connect", f"name={ssid}"]
        subprocess.run(connect_cmd, capture_output=True, check=True)

        # 4. Wait for connection verification
        print("   ⏳ Waiting for IP address...")
        for _ in range(15):
            # Check if we are connected to the specific SSID
            result = subprocess.run(["netsh", "wlan", "show", "interfaces"], capture_output=True, text=True)
            if f"SSID                   : {ssid}" in result.stdout:
                print(f"   ✅ Connected to {ssid}")
                return True
            time.sleep(1)

        print("   ❌ Connection timed out.")
        return False

    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    finally:
        # Cleanup: Remove the temp XML file
        if os.path.exists(filename):
            os.remove(filename)

def get_current_wifi_ssid():
    result = subprocess.run(["netsh", "wlan", "show", "interfaces"], capture_output=True, text=True)
    for line in result.stdout.split('\n'):
        if "SSID" in line and "BSSID" not in line: # Avoid BSSID
            return line.split(":")[1].strip()
    return None