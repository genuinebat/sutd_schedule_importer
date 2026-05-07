import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import icalendar
from pathlib import Path

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

path = Path("./schedule.ics")
cal = icalendar.Calendar.from_ical(path.read_bytes())

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
    service.events().insert(calendarId="greg250977@gmail.com", body=event).execute()
    print("Added " + summary)

print("DONE IMPORTING SCHEDULE")
