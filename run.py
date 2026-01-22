#run.py
import sqlalchemy as sa
from sqlalchemy import orm

from app import create_app, db, socketio
from app.models import User, Ticket

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {'sa': sa, 'orm': orm, 'db': db, 'User': User, 'Ticket': Ticket}

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)