# config.py - Configuration values
import os
from dotenv import load_dotenv

load_dotenv()

# Notion API configuration
NOTION_API_KEY = os.environ.get("NOTION_API_KEY")

# Google Calendar configuration
CALENDAR_ID = "m94qeesb73f76j50sht7ku6tbc@group.calendar.google.com"
SCOPES = ['https://www.googleapis.com/auth/calendar']

# Status to color mapping
STATUS_COLORS = {
    "1. Not started": "11",  # Red
    "2. In progress": "5",   # Orange
    "3. Done": "7",          # Blue
    "4. Submitted": "10"     # Green
}