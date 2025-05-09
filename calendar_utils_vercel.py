# calendar_utils_vercel.py - Adapted for Vercel
import os
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from config import CALENDAR_ID, STATUS_COLORS

def get_calendar_service():
    """Get authenticated Google Calendar service using service account"""
    # For Vercel, we use a service account instead of OAuth flow
    # The credentials JSON is stored as an environment variable
    creds_json = os.environ.get('GOOGLE_SERVICE_ACCOUNT_KEY')
    if not creds_json:
        raise ValueError("Google service account credentials not found")

    # Create credentials from the service account info
    creds = Credentials.from_service_account_info(
        eval(creds_json),
        scopes=['https://www.googleapis.com/auth/calendar']
    )

    # Build the service
    return build('calendar', 'v3', credentials=creds)

def get_color_id_by_status(status):
    """Map task status to Google Calendar color ID"""
    return STATUS_COLORS.get(status, "11")  # Default to red

def find_calendar_event_by_notion_id(notion_id):
    """Find calendar event with the given Notion ID in description"""
    try:
        service = get_calendar_service()
        notion_id_marker = f"notion-id:{notion_id}"

        events_result = service.events().list(
            calendarId=CALENDAR_ID,
            q=notion_id_marker,
            singleEvents=True
        ).execute()

        events = events_result.get('items', [])
        return events[0] if events else None

    except Exception as e:
        print(f"Error finding calendar event: {e}")
        return None

def create_or_update_calendar_event(task_data, notion_id):
    """Create or update a Google Calendar event based on Notion task data"""
    try:
        service = get_calendar_service()

        # Format event title with icon, task name and type
        event_title = f"{task_data['course_icon']} | {task_data['title']} | {task_data['task_type']}"

        # Parse deadline date
        start_date = task_data['deadline'].get('start') if task_data['deadline'] else None
        if not start_date:
            print("No deadline date, skipping calendar event")
            return

        # Add Notion ID to description for future reference
        description = task_data['notes'] or ""
        notion_id_marker = f"\n\nnotion-id:{notion_id}"
        if not description.endswith(notion_id_marker):
            description += notion_id_marker

        # Define event data
        event_data = {
            'summary': event_title,
            'description': description,
            'colorId': get_color_id_by_status(task_data['status']),
            'start': {
                'date': start_date,
                'timeZone': 'America/Santiago',
            },
            'end': {
                'date': start_date,
                'timeZone': 'America/Santiago',
            },
        }

        # Find existing event
        existing_event = find_calendar_event_by_notion_id(notion_id)

        if existing_event:
            # Update existing event
            event = service.events().update(
                calendarId=CALENDAR_ID,
                eventId=existing_event['id'],
                body=event_data
            ).execute()
            print(f"Event updated: {event.get('htmlLink')}")
        else:
            # Create new event
            event = service.events().insert(
                calendarId=CALENDAR_ID,
                body=event_data
            ).execute()
            print(f"Event created: {event.get('htmlLink')}")

    except Exception as e:
        print(f"Error creating/updating calendar event: {e}")

def delete_calendar_event(notion_id):
    """Delete calendar event associated with a Notion page"""
    try:
        service = get_calendar_service()
        existing_event = find_calendar_event_by_notion_id(notion_id)

        if existing_event:
            service.events().delete(
                calendarId=CALENDAR_ID,
                eventId=existing_event['id']
            ).execute()
            print(f"Calendar event deleted for Notion page {notion_id}")
            return True

        return False

    except Exception as e:
        print(f"Error deleting calendar event: {e}")
        return False