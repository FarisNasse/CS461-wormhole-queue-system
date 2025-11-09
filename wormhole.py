import sqlalchemy as sa
import sqlalchemy.orm as orm

from app import create_app, db
from app.models import User, Ticket

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {'sa': sa, 'orm': orm, 'db': db, 'User': User, 'Ticket': Ticket}