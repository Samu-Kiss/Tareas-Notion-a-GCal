import datetime as dt
import os.path

from notion_client import Client
from dotenv import load_dotenv

from flask import Flask, request, jsonify
import threading

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Load environment variables (for Notion API key)
load_dotenv()
notion = Client(auth=os.environ.get("NOTION_API_KEY"))
app = Flask(__name__)
SCOPES = ['https://www.googleapis.com/auth/calendar']

def find_calendar_event_by_notion_id(service, notion_id, calendar_id):
    """Find calendar event with the given Notion ID in description"""
    try:
        # Add a unique identifier in the description we can search for
        notion_id_marker = f"notion-id:{notion_id}"

        # Search in the calendar for events with this marker
        events_result = service.events().list(
            calendarId=calendar_id,
            q=notion_id_marker,
            singleEvents=True
        ).execute()

        events = events_result.get('items', [])
        if events:
            return events[0]
        return None
    except Exception as e:
        print(f"Error finding calendar event: {e}")
        return None

def create_or_update_calendar_event(title, task_type, deadline, notes, status, course_icon, course_name, notion_id):
    """Create or update a Google Calendar event based on Notion task data"""
    try:
        service = get_calendar_service()
        calendar_id = "m94qeesb73f76j50sht7ku6tbc@group.calendar.google.com"

        # Format event title with icon, task name and type
        event_title = f"{course_icon} | {title} | {task_type}"

        # Parse deadline date
        start_date = deadline.get('start') if deadline else None
        if not start_date:
            print("No deadline date, skipping calendar event")
            return

        # Add Notion ID to description for future reference
        description = notes or ""
        notion_id_marker = f"\n\nnotion-id:{notion_id}"
        if not description.endswith(notion_id_marker):
            description += notion_id_marker

        # Define event data
        event_data = {
            'summary': event_title,
            'description': description,
            'colorId': get_color_id_by_status(status),
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
        existing_event = find_calendar_event_by_notion_id(service, notion_id, calendar_id)

        if existing_event:
            # Update existing event
            event = service.events().update(
                calendarId=calendar_id,
                eventId=existing_event['id'],
                body=event_data
            ).execute()
            print(f"Event updated: {event.get('htmlLink')}")
        else:
            # Create new event
            event = service.events().insert(
                calendarId=calendar_id,
                body=event_data
            ).execute()
            print(f"Event created: {event.get('htmlLink')}")

    except Exception as e:
        print(f"Error creating/updating calendar event: {e}")

def get_color_id_by_status(status):
    """Map task status to Google Calendar color ID"""
    status_to_color = {
        "1. Not started": "11",  # Red
        "2. In progress": "6",   # Orange
        "3. Done": "1",          # Blue
        "4. Submitted": "10"     # Green
    }
    return status_to_color.get(status, "11")  # Default to red

def create_calendar_event(title, task_type, deadline, notes, status, course_icon, course_name):
    """Create a Google Calendar event from Notion task data"""
    try:
        service = get_calendar_service()

        # Format event title with icon, task name and type
        event_title = f"{course_icon} | {title} | {task_type}"

        # Parse deadline date
        start_date = deadline.get('start') if deadline else None
        if not start_date:
            print("No deadline date, skipping calendar event creation")
            return

        # Create event with appropriate formatting
        event = {
            'summary': event_title,
            'description': notes or 'Task from Notion',
            'colorId': get_color_id_by_status(status),
            'start': {
                'date': start_date,
                'timeZone': 'America/Santiago',
            },
            'end': {
                'date': start_date,
                'timeZone': 'America/Santiago',
            },
        }

        # Set calendar ID - using primary calendar
        calendar_id = "m94qeesb73f76j50sht7ku6tbc@group.calendar.google.com"

        event = service.events().insert(calendarId=calendar_id, body=event).execute()
        print(f"Event created: {event.get('htmlLink')}")

    except Exception as e:
        print(f"Error creating calendar event: {e}")

def get_course_icon(course_id):
    """Retrieve just the emoji from a course's icon"""
    try:
        # Directly retrieve the course page using its ID
        course_page = notion.pages.retrieve(page_id=course_id)
        icon = course_page.get("icon")

        # Extract just the emoji if the icon exists and is of type emoji
        if icon and icon.get("type") == "emoji":
            return icon.get("emoji")
        return icon
    except Exception as e:
        print(f"Error retrieving course icon: {e}")
        return None


def get_course_name(course_id):
    """Retrieve the name of a course by its page ID"""
    try:
        # Retrieve the course page using its ID
        course_page = notion.pages.retrieve(page_id=course_id)

        # Extract the course title/name using the existing function
        return get_page_title(course_page)
    except Exception as e:
        print(f"Error retrieving course name: {e}")
        return "Unknown Course"


@app.route('/notion-webhook', methods=['POST'])
def notion_webhook():
    # Receive and process webhook data from Notion
    data = request.json
    print("Received webhook from Notion:", data)

    # Extract important information
    event_type = data.get('type')
    entity = data.get('entity', {})
    entity_id = entity.get('id')
    entity_type = entity.get('type')

    # Process different event types
    if event_type in ['page.created', 'page.updated', 'page.properties_updated']:
        try:
            # Get page details from Notion API
            page_data = notion.pages.retrieve(page_id=entity_id)

            # Extract task details and create/update calendar event
            title = get_page_title(page_data)
            task_type = "Unknown Type"
            if page_data.get('properties', {}).get('Type', {}).get('select'):
                task_type = page_data['properties']['Type']['select'].get('name', 'Unknown Type')

            status = "Unknown Status"
            if page_data.get('properties', {}).get('Progress', {}).get('status'):
                status = page_data['properties']['Progress']['status'].get('name', 'Unknown Status')

            deadline = None
            if page_data.get('properties', {}).get('Deadline', {}).get('date'):
                deadline = page_data['properties']['Deadline']['date']

            notes = ""
            if page_data.get('properties', {}).get('notes', {}).get('rich_text'):
                notes_items = page_data['properties']['notes']['rich_text']
                notes = ''.join([item.get('plain_text', '') for item in notes_items])

            course_id = get_course_relation_id(page_data)
            course_icon = "📝"  # Default icon
            course_name = "Unknown Course"

            if course_id:
                course_icon = get_course_icon(course_id) or course_icon
                course_name = get_course_name(course_id)

            print(f"🔔 Task Updated: {course_icon} | {course_name} | {title} | {task_type} | {status}")

            # Create or update the calendar event with the Notion page ID
            create_or_update_calendar_event(title, task_type, deadline, notes, status,
                                           course_icon, course_name, entity_id)
        except Exception as e:
            print(f"Error processing Notion page: {e}")

    elif event_type == 'page.deleted':
        # Delete the corresponding calendar event code (unchanged)
        try:
            service = get_calendar_service()
            calendar_id = "m94qeesb73f76j50sht7ku6tbc@group.calendar.google.com"
            existing_event = find_calendar_event_by_notion_id(service, entity_id, calendar_id)

            if existing_event:
                service.events().delete(calendarId=calendar_id, eventId=existing_event['id']).execute()
                print(f"Calendar event deleted for Notion page {entity_id}")

            print(f"Page {entity_id} was deleted from database {data.get('data', {}).get('parent', {}).get('id')}")
        except Exception as e:
            print(f"Error handling deleted page: {e}")

    return jsonify({"status": "success"}), 200

def get_course_relation_id(page_data):
    """Extract the course relation ID from a Notion page"""
    properties = page_data.get('properties', {})
    course_prop = properties.get('Course')

    if course_prop and course_prop.get('type') == 'relation':
        relations = course_prop.get('relation', [])
        if relations and len(relations) > 0:
            return relations[0].get('id')

    return None

def get_page_title(page_data):
    """Extract the title from a Notion page object"""
    properties = page_data.get('properties', {})

    # Try to find title property (could be "Title", "Name", etc.)
    for prop_name, prop_data in properties.items():
        if prop_data.get('type') == 'title':
            title_items = prop_data.get('title', [])
            title_parts = [item.get('plain_text', '') for item in title_items]
            return ''.join(title_parts)

    return "Untitled"

def get_calendar_service():
    creds = None

    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)

        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return build('calendar', 'v3', credentials=creds)

def list_calendar_events():
    try:
        service = get_calendar_service()

        # Fetch events from the selected calendar
        now = dt.datetime.now().isoformat() + 'Z'
        events_result = service.events().list(
            calendarId="m94qeesb73f76j50sht7ku6tbc@group.calendar.google.com", timeMin=now,
            maxResults=10, singleEvents=True, orderBy='startTime'
        ).execute()
        events = events_result.get('items', [])

        if not events:
            print('No upcoming events found.')
            return

        # Fetch color information
        colors = service.colors().get().execute()
        event_colors = colors.get('event', {})

        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            event_id = event['id']
            summary = event['summary']
            description = event.get('description', 'No description')
            color_id = event.get('colorId')

            color_info = "Default"
            if color_id and color_id in event_colors:
                color_info = f"Color {color_id} ({event_colors[color_id]['background']})"

            print(f"Event ID: {event_id}")
            print(f"Start: {start}")
            print(f"Summary: {summary}")
            print(f"Description: {description}")
            print(f"Color: {color_info}")
            print("-" * 40)

    except HttpError as error:
        print(f'An error occurred: {error}')

def main():
    # Start the Flask server in a separate thread
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=5000, debug=False)).start()
    print("Webhook server started on port 5000")

    # List calendar events
    # list_calendar_events()

if __name__ == '__main__':
    main()