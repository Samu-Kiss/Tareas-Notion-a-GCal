# app.py - Main application with webhook handlers
from flask import Flask, request, jsonify
import threading
from notion_utils import get_page_data, notion
from calendar_utils import create_or_update_calendar_event, delete_calendar_event

app = Flask(__name__)

@app.route('/notion-webhook', methods=['POST'])
def notion_webhook():
    # Receive and process webhook data from Notion
    data = request.json
    print("Received webhook from Notion:", data)

    # Extract important information
    event_type = data.get('type')
    entity = data.get('entity', {})
    entity_id = entity.get('id')

    # Process different event types
    if event_type in ['page.created', 'page.updated', 'page.properties_updated']:
        try:
            # Get task data and create/update calendar event
            task_data = get_page_data(entity_id)

            if task_data:
                print(f"🔔 Task Updated: {task_data['course_icon']} | {task_data['course_name']} | "
                      f"{task_data['title']} | {task_data['task_type']} | {task_data['status']}")

                # Create or update the calendar event with the Notion page ID
                create_or_update_calendar_event(task_data, entity_id)

        except Exception as e:
            print(f"Error processing Notion page: {e}")

    elif event_type == 'page.deleted':
        try:
            # Delete the corresponding calendar event
            deleted = delete_calendar_event(entity_id)
            if deleted:
                print(f"Page {entity_id} was deleted from database {data.get('data', {}).get('parent', {}).get('id')}")
        except Exception as e:
            print(f"Error handling deleted page: {e}")

    return jsonify({"status": "success"}), 200

def main():
    # Start the Flask server in a separate thread
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=5000, debug=False)).start()
    print("Webhook server started on port 5000")

if __name__ == '__main__':
    main()