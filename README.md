# NS_LINK: Automated Router Provisioning System 🚀

## The Problem
Manually configuring hundreds of routers is a nightmare. It involves:
1.  Reading tiny text on labels (SSID, Password, S/N).
2.  Manually connecting to each router's WiFi.
3.  Clicking through a slow web interface (Region, Timezone, etc.).
4.  Typing in new credentials without making mistakes.
5.  Repeating this 500+ times.

## The Solution
**NS_LINK** is a hybrid automation system designed to turn this manual slog into a streamlined assembly line. It consists of two parts:

### 1. The Scanner (Web App) 📸
A Next.js web application (deployed on Vercel) that uses AI to instantly "read" router labels.
*   **Input**: Photos of router labels.
*   **AI**: Extracts Serial Number, Default SSID, and Default Password.
*   **Output**: A clean CSV file (`router_queue.csv`) ready for the bot.

### 2. The Bot (Python Automation) 🤖
A Python script that acts as a virtual robot.
*   **Input**: The `router_queue.csv` file from the Scanner.
*   **Action**: It continuously scans the airwaves for the routers in your queue. When it sees one, it:
    *   Auto-connects to its WiFi.
    *   Runs the setup wizard (Region: Malaysia, Timezone, etc.).
    *   Sets the new SSID and Admin Password.
    *   Verifies the configuration.

---

## 📋 Standard Operating Procedure (SOP)

Follow these steps to configure a batch of routers.

### Phase 1: Data Ingestion (The Scanner)
*Goal: Create a digital list of all routers to be configured.*

1.  **Open the Web App**: Navigate to your Vercel deployment URL.
2.  **Scan Labels**:
    *   Use the **Camera** tab to snap photos of router labels on your phone/laptop.
    *   OR use **Upload** if you have existing photos.
3.  **Verify & Edit**:
    *   The AI will extract the details. Check them quickly.
    *   **CRITICAL**: Enter the **Target SSID** for each router (e.g., "NS Room 801", "Lobby WiFi"). This is what the router *will become*.
4.  **Preview & Download**:
    *   Click **Preview CSV** to double-check your batch.
    *   Click **Download CSV**. This will save `router_queue.csv` to your computer.

### Phase 2: The Factory (The Bot)
*Goal: Let the robot do the work.*

1.  **Prepare the Environment**:
    *   Ensure you have the `router_queue.csv` file in the same folder as `main.py`.
    *   **Power ON** the routers you want to configure. You can do them in batches (e.g., 5-10 at a time).
2.  **Run the Bot**:
    *   Open your terminal (Command Prompt or PowerShell).
    *   Navigate to the project folder.
    *   Run the command:
        ```bash
        python main.py
        ```
3.  **Watch the Magic**:
    *   The bot will say: `🏭 NS ROUTER MILL: FACTORY MODE ACTIVATED`.
    *   It will scan for WiFi networks.
    *   When it finds a match from your CSV, it will say `🎯 MATCH!`.
    *   It will launch a browser window, log in, and click through the setup wizard for you.
    *   **Do not touch the mouse/keyboard** while the browser window is open.
4.  **Completion**:
    *   Once a router is done, the bot will mark it as complete and start looking for the next one.
    *   Label the finished router and move to the next batch.

---

## 🛠️ Setup & Prerequisites (First Time Only)

If you are setting this up on a new laptop, you need:

1.  **Python**: Install Python 3.x from python.org.
2.  **Dependencies**: Open terminal and run:
    ```bash
    pip install playwright pandas requests
    playwright install
    ```
3.  **WiFi Adapter**: The laptop MUST have a working WiFi adapter to scan and connect to routers.

## ⚠️ Troubleshooting

*   **Bot gets stuck on "Region"**: We recently fixed this! Ensure you have the latest version of `router_bot.py`.
*   **"Connection Failed"**: If the bot can't connect to WiFi, move closer to the router or try restarting the script.
*   **AI missed a digit**: Always glance at the "Preview CSV" table before downloading. You can edit the fields directly in the Web App before downloading.

---
*Built for speed. Built for NS.*