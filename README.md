# Wormhole Queue System

**Wormhole Queue System is a web-based tutoring queue for Oregon State University's Physics Help Center that lets students request help and lets Wormhole Assistants manage those requests in a clear, fair order.**

The project modernizes the Wormhole's help-request workflow by connecting student-facing request forms, a public live queue, assistant ticket tools, and administrative records in one maintainable Flask application.

[Try the live site](https://wormhole.physics.oregonstate.edu/) · [Submit a help request](https://wormhole.physics.oregonstate.edu/createticket) · [View the live queue](https://wormhole.physics.oregonstate.edu/livequeue) · [View the source code](https://github.com/FarisNasse/CS461-wormhole-queue-system)

![Blue digital wormhole graphic used as the project header image.](app/static/Updated-Wormhole-Image.png)

## Why this project matters

The Wormhole is a physics collaboration and help center where students may need support from Wormhole Assistants during busy tutoring hours. Without a clear queue, students can be unsure whether their request was seen, assistants can lose track of who should be helped next, and administrators have less visibility into how the center is being used.

Wormhole Queue System gives students a simple way to ask for help, gives assistants a shared workflow for claiming and resolving tickets, and gives administrators tools for account management, queue maintenance, and historical review.

## Key features

- **Student-friendly help requests:** Students can submit a help request from the web by entering their name, physics course, and location. The system also supports requests from physical Wormhole button boxes.
- **Public live queue:** Students can check the live queue to see which requests are waiting and which are currently being handled.
- **Assistant ticket workflow:** Wormhole Assistants can claim tickets, return tickets to the queue, and resolve tickets as helped, duplicate, or no-show.
- **Administrative controls:** Admin users can create individual or batch assistant accounts, manage active users, monitor hardware status, clear or flush queue data, and export archived ticket records.
- **Maintainable project foundation:** The system uses Flask, SQLAlchemy, Flask-Migrate, SocketIO queue updates, CSRF-protected forms, automated tests, linting tools, and deployment documentation so future maintainers can continue improving it.

## Project demo

The demo below shows one of the student request paths: a physical Wormhole button box submitting a help request into the queue.

![Animated demo of a Wormhole table button box submitting a student help request.](assets/button_box.gif)

A typical queue interaction works like this:

1. A student submits a help request from the website or a Wormhole button box.
2. The request appears in the live queue.
3. A Wormhole Assistant claims the ticket and helps the student.
4. The assistant resolves the ticket, and the system keeps the record for review or export.

## How to access or try it

### Live site

The public site is available at: <https://wormhole.physics.oregonstate.edu/>

- Students can use **Submit a Help Request** to enter the queue.
- Students can use **Live Queue** to see current queue activity.
- Wormhole Assistants and administrators need approved accounts to access staff-only tools.

### Local development

To run the project locally:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
flask db upgrade
python run.py
