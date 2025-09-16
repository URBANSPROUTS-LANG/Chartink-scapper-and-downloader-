Chrome Debugging Setup with Selenium

This project automates downloading CSV files from a premium account.

What it does:

Opens Chrome using a dedicated debug profile.

Takes all the links from the target pages and saves them.

Uses a premium account profile to access restricted content.

Downloads CSV files automatically.

This allows you to efficiently collect and download data without manually navigating pages.

---

# 🚀 Chrome Debugging Setup with Selenium

This guide explains how to run Chrome with a remote debugging port, verify it’s working, and set up the required environment for automation.

---

## 🔧 Steps to Run


1. **Kill any existing Chrome processes**

   ```
   taskkill /F /IM chrome.exe /T
   ```

2. **Start Chrome with debugging enabled**

   ```
   "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9233 --remote-allow-origins=* --user-data-dir=C:\chrome_debug --profile-directory="Profile x"
   ```

3. **Verify Chrome is running on port 9233**

   ```
   netstat -ano | findstr :9233
   ```
4 import 
 git clone https://github.com/URBANSPROUTS-LANG/vectras-vm2.git
cd vectras-vm2


---

## ▶️ Run Script
*  **chartink scrapper.py**
* Run the script:
   ```
chartink scrapper

  
*  **9yearscsv.py**
* Run the script:

  ```
  python 9years_csv.py
  ```

---

## 📦 Installation Requirements

Make sure you have the following installed:

* **Python 3.x**
* **Selenium**

  ```
  pip install selenium
  ```
* **ChromeDriver** (matching your installed Chrome version)

  * [Download ChromeDriver](https://chromedriver.chromium.org/downloads)

---

✨ You’re ready to go!


---
Dont to forget
 * to downlaod all scripts and installation requirements
 * change all file paths to work for your computer



