# ICT Technical Assistance Ticketing System

This prototype delivers a lightweight full-stack ticketing system for the Division IT Unit. It includes:

- Ticket intake form for school heads and teachers
- IT dashboard for viewing, filtering, and updating ticket status
- M&E analytics summary for ticket volume and resolution rate

## Features

- Unique tracking ID generation for every submission
- Persistent SQLite storage for ticket records
- Dynamic filters by school and issue category
- Status transitions across Pending, In Progress, and Resolved
- Analytics summary with resolution rate and risk indicator
- IT-only access control for the dashboard and analytics
- Explicit consent requirement before ticket submission
- Minimum-data exposure for IT dashboard views
- Hashed IT department password check for safer authentication

## Local Setup

1. Open the project folder.
2. Install Flask if needed:
   ```bash
   python3 -m pip install flask
   ```
3. Start the app:
   ```bash
   python3 app.py
   ```
4. Open the browser at http://127.0.0.1:5000/

## Running Tests

```bash
python3 -m unittest discover -s tests -v
```

## Technical Questionnaire

### 1. System Stack Architecture
The prototype uses Python with Flask for the backend, SQLite for persistent storage, and a single-page HTML/JavaScript interface for the frontend. This stack was chosen because it is fast to set up, lightweight, and well-suited for a strict 4-hour development window.

### 2. Data Privacy & Policy Compliance
The application uses a simple server-side validation model and stores all tickets in a local database. School personnel submit their own tickets via the intake form, while the dashboard and analytics are restricted to authorized IT department users. The prototype now requires explicit consent before a ticket is accepted, uses a hashed password verification step for IT access, and exposes only the minimum ticket data needed for dashboard operations.

### 3. M&E Analytics Logic
The analytics route calculates totals and resolution rate safely by checking whether the ticket count is zero before dividing. The system also records creation and update timestamps for each ticket so status lifecycle changes can be tracked over time for delivery-speed monitoring.

## Privacy Notes

- Ticket submission requires explicit user consent.
- Dashboard and analytics access are restricted to authorized IT department users.
- The system exposes only the minimum ticket details required for operational use.
- IT authentication uses a hashed password check for safer access control.
