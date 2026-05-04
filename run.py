# run.py
import os

import sqlalchemy as sa
from dotenv import load_dotenv
from sqlalchemy import orm

from app import create_app, db, socketio
from app.models import Skipped, Ticket, User

result = load_dotenv("wormhole.env")
os.environ.setdefault("ALLOW_SQLITE_FALLBACK", "1")


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
    socketio.run(app, debug=True, host="0.0.0.0", port=5000)
