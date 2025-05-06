# notion_utils.py - Notion related functions
from notion_client import Client
from config import NOTION_API_KEY

notion = Client(auth=NOTION_API_KEY)

def get_page_title(page_data):
    """Extract the title from a Notion page object"""
    properties = page_data.get('properties', {})

    for prop_name, prop_data in properties.items():
        if prop_data.get('type') == 'title':
            title_items = prop_data.get('title', [])
            title_parts = [item.get('plain_text', '') for item in title_items]
            return ''.join(title_parts)

    return "Untitled"

def get_course_relation_id(page_data):
    """Extract the course relation ID from a Notion page"""
    properties = page_data.get('properties', {})
    course_prop = properties.get('Course')

    if course_prop and course_prop.get('type') == 'relation':
        relations = course_prop.get('relation', [])
        if relations and len(relations) > 0:
            return relations[0].get('id')

    return None

def get_course_icon(course_id):
    """Retrieve just the emoji from a course's icon"""
    try:
        course_page = notion.pages.retrieve(page_id=course_id)
        icon = course_page.get("icon")

        if icon and icon.get("type") == "emoji":
            return icon.get("emoji")
        return icon
    except Exception as e:
        print(f"Error retrieving course icon: {e}")
        return None

def get_course_name(course_id):
    """Retrieve the name of a course by its page ID"""
    try:
        course_page = notion.pages.retrieve(page_id=course_id)
        return get_page_title(course_page)
    except Exception as e:
        print(f"Error retrieving course name: {e}")
        return "Unknown Course"

def get_page_data(page_id):
    """Get a Notion page and extract relevant task data"""
    try:
        page_data = notion.pages.retrieve(page_id=page_id)

        # Extract basic task details
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

        # Get course information
        course_id = get_course_relation_id(page_data)
        course_icon = "📝"  # Default icon
        course_name = "Unknown Course"

        if course_id:
            course_icon = get_course_icon(course_id) or course_icon
            course_name = get_course_name(course_id)

        return {
            'title': title,
            'task_type': task_type,
            'status': status,
            'deadline': deadline,
            'notes': notes,
            'course_icon': course_icon,
            'course_name': course_name
        }

    except Exception as e:
        print(f"Error getting page data: {e}")
        return None