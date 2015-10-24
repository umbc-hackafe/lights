#!/usr/bin/python
import serial
import time
import os
import random
from animations import *

devices = os.listdir("/dev/")
serialDev = None
for i in devices:
  if "ttyACM" in i or "hidraw" in i:
    serialDev = os.path.join("/dev/", i)
print(serialDev)
serialPort = serial.Serial(serialDev)

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

anim = Animation([Frame([Segment(range(i%3, 50, 3), 0xFF0000),
                        Segment(range((i+1)%3, 50, 3), 0xFF7F00),
                         Segment(range((i+2)%3, 50, 3), 0x7500B0)]) for i in range(3)]).render()

while True:
  put_animation(anim, setLight)
