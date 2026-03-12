# run.py
import os

import sqlalchemy as sa
from sqlalchemy import orm

from app import create_app, db, socketio
from app.models import Skipped, Ticket, User

app = create_app()


@app.shell_context_processor
def make_shell_context():
    return {
        "sa": sa,
        "orm": orm,
        "db": db,
        "User": User,
        "Ticket": Ticket,
        "Skipped": Skipped,
    }


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    socketio.run(app, debug=debug, host="0.0.0.0", port=port)
