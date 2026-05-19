from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
import shutil
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import icalendar
from pathlib import Path

service = ChromeService(ChromeDriverManager().install())
options = webdriver.ChromeOptions()

options.add_experimental_option("detach", True)

downloads_folder = os.path.join(os.path.expanduser("~"), "Downloads")

prefs = {
    "download.default_directory": downloads_folder,
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "safebrowsing.enabled": True
}
options.add_experimental_option("prefs", prefs)

browser = webdriver.Chrome(service=service, options=options)

URL = "https://myportal.sutd.edu.sg"

browser.get(URL)

WebDriverWait(browser, 300).until(lambda d: "HCCC_ENROLLMENT" in d.current_url)

WebDriverWait(browser, 20).until(EC.frame_to_be_available_and_switch_to_it((By.ID, "ptifrmtgtframe")))

inject_btn = """
let btn = document.createElement("button");
btn.innerHTML = "IMPORT TO G-CALENDAR";

btn.style.cssText = "position:fixed; top:20px; right:20px; z-index:999999; padding:15px 25px; background-color:#4f772d; color:white; font-size:18px; font-weight:bold; cursor:pointer; border-radius:8px; border:2px solid black; box-shadow: 3px 3px 10px rgba(0,0,0,0.5);";

window.import = false;

btn.onclick = function() {
    window.import = true;
    btn.innerHTML = "IMPORTING...";
    btn.style.backgroundColor = "#f0ad4e";
};

// Add the button to the webpage
document.body.appendChild(btn);
"""

browser.execute_script(inject_btn)

WebDriverWait(browser, 3600).until(lambda d: d.execute_script("return window.import === true;"))

browser.switch_to.default_content()

with open("extractor.js", "r", encoding="utf-8") as f:
    js_code = f.read()

browser.execute_script(js_code)

waited, timeout = 0, 300

ics_file = os.path.join(downloads_folder, "schedule.ics")

destination = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schedule.ics")

WebDriverWait(browser, 300).until(lambda d: d.execute_script("return window.icsReady === true;"))

ics_text = browser.execute_script("return window.icsData;")

browser.quit()

SCOPES = ["https://www.googleapis.com/auth/calendar"]
creds = None

if os.path.exists("token.json"):
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)

if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(
          "credentials.json", SCOPES
        )
        creds = flow.run_local_server(port=0)

    with open("token.json", "w") as token:
        token.write(creds.to_json())

service = build("calendar", "v3", credentials=creds)

cal = icalendar.Calendar.from_ical(ics_text)

for e in cal.events:
    if not e.get("SUMMARY"):
        continue
    
    summary = " ".join(e.get("SUMMARY").split(" ")[3:])
    if "Cohort Based Learning" in summary: 
        summary = summary.replace("Cohort Based Learning", "Class")
        color_id = 9
    elif "Lecture" in summary:
        color_id = 8
    else:
        color_id = 3

    location = e.get("LOCATION")
    
    start = e.get("DTSTART").dt.isoformat()
    end = e.get("DTEND").dt.isoformat()
    
    event = {
        "summary": summary,
        "location": location,
        "colorId": color_id,
        "description": "",
        "start": {
            "dateTime": start,
            "timeZone": "Asia/Singapore",
        },
        "end": {
            "dateTime": end,
            "timeZone": "Asia/Singapore",
        },
        "recurrence": [],
        "attendees": [],
        "reminders": {
            "useDefault": False,
            "overrides": [
                {"method": "popup", "minutes": 30},
            ],
        },
    }
    service.events().insert(calendarId="primary", body=event).execute()
    print("Added " + summary)

os.remove(destination)

print("DONE IMPORTING SCHEDULE")