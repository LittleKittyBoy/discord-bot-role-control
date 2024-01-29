import logging
from flask import Flask

# Set the Flask app
app = Flask(__name__)

# Suppress Flask's built-in logger messages
log = logging.getLogger('Uptime Server')
log.setLevel(logging.ERROR)  # Change this to logging.CRITICAL to hide all logs

# Your route definition goes here
@app.route('/')
def index():
    return '200 OK', 200

# Start the server
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8085)