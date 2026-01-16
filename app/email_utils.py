from flask import render_template
from flask_mail import Message
from app import mail, db
from app.models import Ticket, User

def send_unclosed_ticket_reminders():
    # 1. Identify all unclosed tickets (live or current)
    unclosed_tickets = Ticket.query.filter(Ticket.status != 'closed').all()
    
    if not unclosed_tickets:
        return

    # 2. Group tickets by the assigned TA
    reminders = {}
    unassigned_tickets = []

    for ticket in unclosed_tickets:
        if ticket.status == 'current' and ticket.wormhole_assistant:
            wa_email = ticket.wormhole_assistant.email
            if wa_email not in reminders:
                reminders[wa_email] = []
            reminders[wa_email].append(ticket)
        elif ticket.status == 'live':
            unassigned_tickets.append(ticket)

    # 3. Email TAs about their specific 'current' tickets
    for email, tickets in reminders.items():
        msg = Message("Action Required: Unclosed Wormhole Tickets",
                      sender="noreply@wormhole.osu.edu",
                      recipients=[email])
        
        student_list = "\n".join([f"- {t.student_name}" for t in tickets])
        
        msg.body = (f"Hello,\n\nYou have {len(tickets)} tickets still marked as 'current':\n"
                    f"{student_list}\n\n"
                    f"Please close them once help is finished.")
        
        mail.send(msg)

    # 4. Email all TAs/Admins if there are 'live' tickets waiting too long
    if unassigned_tickets:
        all_ta_emails = [u.email for u in User.query.filter_by(is_admin=True).all()]
        if all_ta_emails:
            msg = Message("Alert: New Tickets in Queue",
                          sender="noreply@wormhole.osu.edu",
                          recipients=all_ta_emails)
            msg.body = f"There are {len(unassigned_tickets)} tickets currently waiting in the live queue."
            mail.send(msg)