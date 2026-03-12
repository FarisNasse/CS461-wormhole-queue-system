# application.py
# AWS Elastic Beanstalk entry point.
# EB's Python platform looks for a file named application.py and a WSGI
# callable named application.  We also expose the SocketIO server so that
# the Procfile can start it with eventlet.
from app import create_app, socketio

application = create_app()

if __name__ == "__main__":
    socketio.run(application, host="0.0.0.0", port=5000)
