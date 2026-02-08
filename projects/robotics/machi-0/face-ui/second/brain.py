from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import sys

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

@app.route('/')
def index():
    return render_template('looi.html')

@app.route('/emotion/<type>')
def trigger_emotion(type):
    socketio.emit('change_emotion', {'emotion': type})
    return f"Status: {type}", 200

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)