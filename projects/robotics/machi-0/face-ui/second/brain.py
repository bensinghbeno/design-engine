from flask import Flask, render_template
from flask_socketio import SocketIO
import logging

# Disable heavy logging to keep terminal clean
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

@app.route('/')
def index():
    return render_template('looi.html')

@app.route('/emotion/<type>')
def trigger_emotion(type):
    print(f">>> Switching Looi to: {type}")
    socketio.emit('change_emotion', {'emotion': type})
    return f"Looi status: {type}\n", 200

if __name__ == '__main__':
    print("Looi Brain Active on http://localhost:5000")
    socketio.run(app, host='0.0.0.0', port=5000)