from flask import Flask
from flask_socketio import SocketIO, send, join_room, leave_room, emit
from flask_cors import CORS

from database import connect_redis
from config.freeflow_config import SOCKET_SECRET
from api import api_blueprint, add_message, get_team_data, create_team, join_team, is_3bot_user

import logging
import os

logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))

app = Flask(__name__)
app.register_blueprint(api_blueprint)

app.config['SECRET_KEY'] = SOCKET_SECRET

CORS(app)
app.config["CORS_HEADERS"] = "Content-Type"
socketio = SocketIO(app, cors_allowed_origins="*")


@socketio.on('connect')
def connect_socket():
    print("Client connected")


@socketio.on('disconnect')
def disconnect_socket():
    print('Client disconnected')


@socketio.on('message')
def handle_message(data):
    connect_redis()
    emit('message', data, room=data['channel'])
    add_message(data['channel'], data)


@socketio.on('signal')
def handle_signal(data):
    connect_redis()
    emit('signal', data)


@socketio.on('join')
def join_chat(data):
    connect_redis()
    team_name = data['room']
    team = get_team_data(team_name)
    username = data['name']
    if is_3bot_user(data) is False:
        emit('error', {'error': 'Failed to verify {}'.format(username)})
        return
    if team is None:
        create_team(data)
    else:
        join_team(team, username)
    join_room(team_name)
    send(username + ' has entered the room.', room=team_name)


@socketio.on('leave')
def leave_chat(data):
    username = data['name']
    room = data['channel']
    leave_room(room)
    send(username + ' has left the room.', room=room)


if __name__ == '__main__':
    socketio.run(app, debug=True)
