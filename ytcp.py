#!/usr/bin/env python3

import mpv
import random
import pickle
from youtube_dl import YoutubeDL
from flask import Flask, render_template, request, Response
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config.from_pyfile("ytcp.cfg")
socketio = SocketIO(app, async_mode='threading')

title = ""
songs = []
try:
    with open("songs.p", "rb") as f:
        songs = pickle.load(f)
except Exception as e:
    print("Missing/invalid songs.p file, skipping: " + str(e))
end_handled = False
ydl = YoutubeDL({ 'format': 'bestaudio/best' })

def ydl_extract(url):
    return ydl.extract_info(url, download=False)

def next():
    global title
    try:
        song = random.choice(songs)
        title = song[1]['title']
        player.play(song[1]['url'])
    except IndexError:
        title = ''
    socketio.emit('next', title, broadcast=True)

def changed_songs():
    try:
        with open("songs.p", "wb") as f:
            pickle.dump(songs, f)
    except Exception as e:
        print("Could not save to songs.p, skipping: " + str(e))
    emit('playlist', songs, broadcast=True)

def mpv_log(loglevel, component, message):
    print('[{}] {}: {}'.format(loglevel, component, message))

def mpv_event_handler(event):
    if event['event_id'] == mpv.MpvEventID.PAUSE:
        socketio.emit('toggle', False)
    elif event['event_id'] in (mpv.MpvEventID.UNPAUSE, mpv.MpvEventID.START_FILE):
        socketio.emit('toggle', True)
    elif event['event_id'] == mpv.MpvEventID.IDLE:
        next()

def mpv_observe_volume(level):
    if level:
        socketio.emit('volume', level)
    else:
        socketio.emit('volume', 0)

player = mpv.MPV('no-video', log_handler=mpv_log, ytdl=False)
player.register_event_callback(mpv_event_handler)
player.observe_property('volume', mpv_observe_volume)

@app.route("/")
def index():
    auth = request.authorization
    if not auth or auth.password != app.config['PASS']: 
        return Response(
        'You must log in to access this page.', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'})
    return render_template('index.html')

@socketio.on('connect')
def connect():
    emit('toggle', not player.pause)
    emit('next', title)
    emit('playlist', songs)
    if player.volume:
        emit('volume', player.volume)
    else:
        emit('volume', 0)

@socketio.on('toggle')
def toggle():
    player.pause = not player.pause

@socketio.on('skip')
def skip():
    next()

@socketio.on('add')
def add(song):
    try:
        r = ydl_extract(song)
        if r.get('_type', 'video') != 'video':
            emit('ytcp-error', 'Non-video ({}) link is not supported'.format(r['_type']))
            return
        songs.append([song, r])
        changed_songs()
    except:
        emit('ytcp-error', 'Failed to extract audio URL for {}'.format(song))

@socketio.on('remove')
def remove(song):
    global songs
    songs = list(filter(lambda x: x[0] != song, songs))
    changed_songs()

@socketio.on('volume')
def volume(level):
    player.volume = level

if __name__ == '__main__':
    socketio.run(app)

# vim: ts=4 sw=4 et ai
