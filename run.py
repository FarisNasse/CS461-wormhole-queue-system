#run.py
import sqlalchemy as sa
from sqlalchemy import orm

from app import create_app, db
from app.email_utils import send_unclosed_ticket_reminders
from app.models import User, Ticket

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {'sa': sa, 'orm': orm, 'db': db, 'User': User, 'Ticket': Ticket}

@app.cli.command("send-reminders")
def send_reminders_command():
    """Run the unclosed ticket reminder logic."""
    with app.app_context():
        try:
            count = send_unclosed_ticket_reminders()
            if count > 0:
                print(f"Successfully sent {count} reminder email(s).")
            else:
                print("No unclosed tickets found. No emails sent.")
        except Exception as e:
            print(f"Error while sending reminders: {e}")

if __name__ == '__main__':
    app.run(debug=True)