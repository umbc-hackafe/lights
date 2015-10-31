#!/usr/bin/python
import serial
import time
import os
import threading
import random
import flask
from flask import request
import json
from animations import *

devices = os.listdir("/dev/")
serialDev = None
for i in devices:
  if "ttyACM" in i or "hidraw" in i:
    serialDev = os.path.join("/dev/", i)
print(serialDev)
serialPort = serial.Serial(serialDev)

DEFAULT_ANIMATION = Animation([Frame([Segment(color=0xFFFFFF), Segment(63, brightness=255)])])

lock = threading.Lock()
animations = []
saved_animations = {}

if not os.path.exists(".saved_animations"):
  os.makedirs(".saved_animations")

for fname in (g for g in os.listdir(".saved_animations") if os.path.isfile(os.path.join(".saved_animations", g))):
  with open(os.path.join(".saved_animations", fname)) as f:
    saved_animations[os.path.splitext(os.path.basename(fname))[0].capitalize()] = deserialize(json.load(f))

def setLight(id, brightness, r, g, b):
  #print(bytes([255, 255, id, brightness, r, g, b]))
  serialPort.write(bytes([255, 255, id, brightness, r, g, b]))

def fadeInOut(fadeTime=1):
  for i in range(255):
    setLight(63, i, 0, 0, 0)
    time.sleep(fadeTime/512)
  for i in range(255, 0, -1):
    setLight(63, i, 0, 0, 0)
    time.sleep(fadeTime/512)

def randomPrimary():
  for i in range(50):
    data = [i, 0, 0, 0, 0]
    data[2+random.randint(0, 2)] += 15
    setLight(*data)

def randomSaturated():
  for i in range(50):
    data = [i, 0, 0, 0, 0]
    for j in range(3):
      if random.random() > 0.5:
        data[2+j] += 15
    setLight(*data)

def randomColors():
  for i in range(50):
    data = [i, 0, 0, 0, 0]
    for j in range(3):
      data[2+j] += random.randint(0,15)
    setLight(*data)

# returns a list of segments
def color_wheel(colors, duration):
  size = len(colors)
  return Animation([Frame([Segment(range((i+j)%size, 50, size), colors[j]) for j in range(size)], duration=duration) for i in range(size)])

anim = color_wheel(list(reversed([0xFF0000, 0xFF7F00, 0xFFFF00, 0x00FF00, 0x0000FF, 0xFF00FF])), .085).render()

app = flask.Flask(__name__, static_folder='web')

@app.route("/add_animation", methods=['POST'])
def add_animation(index=None):
  global animations
  data = request.get_json(force=True)
  if data:
    anim = deserialize(data)
  else:
    raise ValueError("NEED DATA")

  save = request.args.get('save')
  name = request.args.get('name')

  if save and name:
    with open(".saved_animations/{}.json".format(name), 'w') as f:
      json.dump(anim.serialize(), f)
      saved_animations[name] = anim

  with lock:
    if index is None:
      animations.append(anim)
    else:
      animations = animations[:index] + [anim] + animations[index:]

  return flask.json.jsonify({"status": "success"})

@app.route('/add_saved_animation/<name>', methods=['POST'])
def add_saved_animation(name, index=None):
  global animations

  name = name.replace('_', ' ')

  if name not in saved_animations:
    raise ValueError("No animation named {} found".format(name))

  anim = saved_animations[name]

  with lock:
    if index is None:
      animations.append(anim)
    else:
      animations = animations[:index] + [anim] + animations[index:]

  return flask.json.jsonify({"status": "success"})

@app.route('/remove_animation/<int:index>', methods=['POST'])
def remove_animation(index):
  with lock:
    if index < 0 or index > len(animations):
      raise IndexError("Index must be between 0 and {}".format(len(lock)-1))

    del animations[index]

  return flask.json.jsonify({"status": "success"})

@app.route('/clear')
def clear():
  global animations
  with lock:
    animations = []

  return flask.json.jsonify({"status": "success"})

@app.route('/animations')
def get_animations():
  with lock:
    anims = list(animations)

  return flask.json.jsonify([anim.serialize() for anim in anims])

@app.route('/saved_animations')
def get_saved_animations():
  return flask.json.jsonify({"animations": list(saved_animations.keys())})

@app.route('/')
def index():
  return app.send_static_file('index.html')

@app.route('/web/<path:path>')
def send_file(path):
  return flask.send_from_directory('./web', path)

def bg_thread():
  while True:
    anims = []
    with lock:
      anims = list(animations)

    if anims:
      for animation in anims:
        put_animation(animation.render(), setLight)
    else:
      put_animation(DEFAULT_ANIMATION.render(), setLight)

threading.Thread(target=bg_thread, daemon=True).start()

app.run('0.0.0.0', port=80, debug=True)
