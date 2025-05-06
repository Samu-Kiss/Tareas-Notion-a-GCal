# 📅 Notion to Google Calendar Integration

## 🚀 Overview
A serverless application that automatically syncs tasks from Notion to Google Calendar. When you create, update, or delete a task in your Notion database, the corresponding event in Google Calendar is created, updated, or removed—keeping your deadlines and to-dos perfectly in sync.

## ✨ Features
- **Real-time synchronization**: Tasks created, updated, or deleted in Notion are immediately reflected in Google Calendar.  
- **Task metadata**: Calendar events include all relevant task information (title, type, status, deadline, notes).  
- **Course organization**: Events are labeled with course names and icons for easy differentiation.  
- **Serverless deployment**: Runs on Vercel, so you don’t have to manage servers.

## 💻 Technologies Used
![Notion](https://img.shields.io/badge/Notion-000000?style=for-the-badge&logo=notion&logoColor=white)  
![Google Calendar](https://img.shields.io/badge/Google_Calendar-4285F4?style=for-the-badge&logo=google-calendar&logoColor=white)  
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)  
![Flask](https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white)  
![Vercel](https://img.shields.io/badge/Vercel-000000?style=for-the-badge&logo=vercel&logoColor=white)  

## ℹ️ About
This integration was created to eliminate manual calendar updates by bridging Notion’s task management with Google Calendar’s scheduling power. Perfect for students, project managers, and anyone who relies on deadlines.

## 🔍 How It Works
1. **Webhook Reception**  
   Notion fires a webhook whenever a task is created, updated, or deleted in your database.  
2. **Data Processing**  
   A serverless function on Vercel processes the webhook, extracts task details via the Notion API, and formats them for Google Calendar.  
3. **Calendar Management**  
   Depending on the action, the function creates, updates, or deletes the corresponding Google Calendar event using the Calendar API.

## 🛠️ Setup Instructions

### Prerequisites
- A Notion account with a task database  
- A Google Cloud project with the Calendar API enabled  
- A Vercel account  

### Step 1: Notion Integration Setup
1. Go to [notion.so/my-integrations](https://www.notion.so/my-integrations) and create a new integration.  
2. Grant **Read**, **Insert**, and **Update** content capabilities.  
3. Share your task database with the integration.  
4. Configure a webhook in Notion pointing to your Vercel function URL.

### Step 2: Google Calendar Setup
1. In the Google Cloud Console, create a service account.  
2. Download the JSON key file for that account.  
3. Enable the Google Calendar API for your project.  
4. Share your target calendar with the service account’s email address.

### Step 3: Deployment
1. Fork this repository.  
2. Connect your fork to Vercel.  
3. In your Vercel project settings, add these environment variables:  
   - `NOTION_API_KEY` – Your Notion integration secret  
   - `CALENDAR_ID` – Your Google Calendar ID  
   - `GOOGLE_SERVICE_ACCOUNT_KEY` – Paste the contents of your service account JSON file  
4. Deploy to Vercel.  
5. Update the Notion webhook URL to match your deployed Vercel function endpoint.

## 🐛 Troubleshooting
- **404 Errors**: Make sure your Notion database is shared with the integration.  
- **Missing Events**: Check Vercel logs for errors—common causes are malformed payloads or missing env vars.  
- **Permission Denied**: Ensure the Google service account has “Make changes to events” permission on the calendar.

## 🏗️ Technical Architecture
- **Backend**: Python + Flask serverless function  
- **APIs**: Notion API & Google Calendar API  
- **Deployment**: Serverless on Vercel  
- **Authentication**: Notion API key & Google service account JSON  
