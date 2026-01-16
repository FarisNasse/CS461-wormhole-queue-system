from flask import current_app
from flask_mail import Message
from sqlalchemy.orm import joinedload
from app import mail, db
from app.models import Ticket, User

def send_unclosed_ticket_reminders():
    # 1. Efficiently identify all unclosed tickets and their assigned assistants
    unclosed_tickets = (
        Ticket.query.options(joinedload(Ticket.wormhole_assistant))
        .filter(Ticket.status != 'closed')
        .all()
    )
    
    if not unclosed_tickets:
        return 0

    reminders = {}
    unassigned_tickets = []
    emails_sent = 0

    # 2. Group tickets
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
                      sender=current_app.config['MAIL_DEFAULT_SENDER'],
                      recipients=[email])
        
        student_list = "\n".join([f"- {t.student_name} ({t.physics_course})" for t in tickets])
        msg.body = (f"Hello,\n\nYou have {len(tickets)} tickets still marked as 'current':\n"
                    f"{student_list}\n\n"
                    f"Please close them once help is finished.")
        mail.send(msg)
        emails_sent += 1

    # 4. Email Admins about unassigned 'live' tickets
    if unassigned_tickets:
        all_admin_emails = [u.email for u in User.query.filter_by(is_admin=True).all() if u.email]
        if all_admin_emails:
            msg = Message("Alert: New Tickets in Queue",
                          sender=current_app.config['MAIL_DEFAULT_SENDER'],
                          recipients=all_admin_emails)
            
            student_list = "\n".join([f"- {t.student_name} (Course: {t.physics_course})" for t in unassigned_tickets])
            msg.body = (f"Hello,\n\nThere are {len(unassigned_tickets)} tickets currently waiting in the live queue:\n"
                        f"{student_list}\n\n"
                        f"Please review the queue and ensure these students are helped.")
            mail.send(msg)
            emails_sent += 1
            
    return emails_sent