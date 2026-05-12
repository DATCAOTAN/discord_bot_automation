# Project Overview and Run Guide

## System Description
This project is a desktop automation system that manages multiple Discord accounts to join servers and send predefined tasks. It uses a wxPython-based UI to configure profiles, proxies, and task inputs, then drives Firefox via Selenium to perform account login, Hotmail verification flows, and Discord actions. Account credentials and state are stored in Google Sheets; the bot reads the sheet per account, performs actions, and writes updates back. The system supports multi-threaded execution, status tracking in Excel, and proxy rotation (static or dynamic) with health checks.

Key features:
- Multi-account automation with thread-based scheduling and per-thread status tracking.
- Google Sheets integration for account data, password updates, and audit logging.
- Hotmail login and Discord password reset flow with 2FA token fetch.
- Proxy management (static/dynamic) and UI controls for runtime configuration.
- Task composition via text/CSV input and automated server join/interaction flows.

## 1) Prerequisites
- Python 3.9+ installed
- Firefox installed
- GeckoDriver available (path used by your profiles)
- Google Service Account JSON for Sheets API

## 2) Install dependencies
```powershell
pip install -r requirements.txt
```

## 3) Set environment variables
Set these before running (examples use PowerShell):

```powershell
$env:GOOGLE_SERVICE_ACCOUNT_FILE="D:\path\credentials.json"
$env:GOOGLE_SHEET_ID="YOUR_SHEET_ID"
$env:BOT_EXCEL_PATH="D:\path\Choose_Profile_Do_Task.xlsx"
$env:BOT_ERROR_LOG_PATH="D:\path\Error_GPM.xlsx"
$env:BOT_CAPTCHA_EXT_URL="moz-extension://.../popup/index.html"
```

Notes:
- `GOOGLE_SERVICE_ACCOUNT_FILE` must be the full path to your Google service account JSON file.
- `GOOGLE_SHEET_ID` is the ID in the Google Sheets URL.
- `BOT_EXCEL_PATH` and `BOT_ERROR_LOG_PATH` are optional but recommended for the UI defaults.
- `BOT_CAPTCHA_EXT_URL` is optional; leave empty if you do not use a captcha extension.

## 4) Prepare profiles
Make sure each profile folder includes:
- Firefox binary path
- GeckoDriver path
- Profile data folder

## 5) Run the app
```powershell
python main.py
```

## 6) Configure in UI
- Select Excel and Error Log files
- Select Google API JSON (same as `GOOGLE_SERVICE_ACCOUNT_FILE`)
- Enter Sheet ID (same as `GOOGLE_SHEET_ID`)
- Choose profiles and proxy settings
- Click Run

## 7) Optional: Build exe
```powershell
pyinstaller --onefile --console main.py
```

## 8) Troubleshooting
- If Google Sheets auth fails, re-check the JSON path and Sheet ID env vars.
- If profiles fail to load, verify Firefox and GeckoDriver paths in your profile folders.
- If proxy errors occur, verify proxy host/port and connectivity.
