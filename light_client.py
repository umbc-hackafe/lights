#!/usr/bin/env python
from animations import *
import requests
import logging
import random
import json
import sys

logging.basicConfig(level=logging.DEBUG)

animation = "off"

if len(sys.argv) >= 3:
  animation = sys.argv[2]

# returns a list of segments
def color_wheel(colors, duration, start=0, end=50, reverse=False):
  size = len(colors)
  if reverse:
    return Animation([Frame([Segment(range(start+(i+j)%size, end, size), colors[j]) for j in range(size)], duration=duration) for i in range(size, 0, -1)])
  else:
    return Animation([Frame([Segment(range(start+(i+j)%size, end, size), colors[j]) for j in range(size)], duration=duration) for i in range(size)])

def wave(states, duration):
  states = states + states[1:-1][::-1]
  states = [{'color': state} if isinstance(state, int) else state for state in states] 
  size = len(states)
  return Animation([Frame([Segment(range((i+j)%size, 50, size), **(states[j%size])) for j in range(size)], duration=duration) for i in range(size)])

def spread_colors(colors, probs=None, duration=1):
  if probs is None:
    probs = [1 / len(colors)] * len(colors)

  color_map = {c: [] for c in colors}
  for l in range(50):
    n = random.random()
    s = 0
    for col, prob in zip(colors, probs):
      s += prob
      if n <= s:
        color_map[col].append(l)
        break
      s += prob

  return Frame([Segment(color_map[c], color=c) for c in colors], duration=duration)

def shuf(l):
  n = list(l)
  random.shuffle(n)
  return n

def iprint(n, **kwargs):
  print(n, dict(**kwargs))
  return n

# size of each block of color in the vee, and the list of colors
def vee(csize, colors, duration=.1, direction="in", center=25):
  return merge_animations(
    color_wheel(list(reversed([val for val in colors for _ in range(csize)])), duration, start=center, end=50, reverse=(direction=="in")),
    color_wheel([val for val in reversed(colors) for _ in range(csize)], duration, start=0, end=center, reverse=(direction=="out")))

ANIM_MAP = {
  "rainbow1": color_wheel(list([0xFF0000, 0xFF7F00, 0xFFFF00, 0x00FF00, 0x0000FF, 0xFF00FF]), .085),
  "on": Animation([Frame([Segment(color=0xFFFFFF)])]),
  "off": Animation([Frame([Segment(color=0x000000), Segment([63], brightness=0)])]),
  "xmas": Animation(
    # Slow, Alternating Red-Green Pattern
    [Frame([Segment(range(0, 50, 2), color=0xFF0000),
            Segment(range(1, 50, 2), color=0x00FF00)],
           duration=.7),

     Frame([Segment(range(0, 50, 2), color=0x00FF00),
            Segment(range(1, 50, 2), color=0xFF0000)],
           duration=.7)
    ] * 3 +

    # Twinkly Blue Lights
    [Frame([Segment(range((j+i)%5, 50, 5), color=0x4444FF, brightness=max(16, j*32)) for j in range(5)], duration=.1) for i in range(0, 15, 3)] * 5 +

    # Alternating Red-Green fade-in/out
    [Frame([Segment(range(0, 50, 2), color=0xFF0000, brightness=64+b),
            Segment(range(1, 50, 2), color=0x00FF00, brightness=64-b)], duration=.01) for b in list(range(-64, 64, 8)) + list(range(64, -64, -8))] * 10 +

    # Wavy blue lights
    [wave([{"color":0x4444FF, "brightness":i} for i in range(16, 128, 28)], duration=.05)] * 10 +

    # Random christmas-light colors
    [spread_colors(shuf([0xFFFF00, 0xFF0000, 0x00FF00, 0x0000FF, 0x8000FF, 0xFF7F00]), duration=1.1) for _ in range(30)] +

    # Oscillating V-pattern in red-green
    [vee(4, [0xFF0000, 0x00FF00], .05, d, center=18) for d in ("in", "out") for _ in range(5)] * 5 +

    # Inward V-pattern in blue
    [vee(1, [int(0x4444FF * i/10) for i in range(10)], .05, center=18)] * 10
  ),
  "rainbow": color_wheel(list(reversed([val for val in [0x800000, 0xFF7F00, 0xFFFF00, 0x00FF00, 0x00FFFF, 0x0000FF, 0x19009F, 0xFF00FF] for _ in (0,1)])), .05),
  "alt-rbvee": Animation([vee(4, [0xFF0000, 0x00FFFF], .05, d) for d in ("in", "out") for _ in range(5)]),
  "rbvee": vee(4, [0xFF0000, 0x00FFFF], .05, "in")
}

anim = ANIM_MAP[animation]

data = json.dumps(anim.serialize())

requests.get('http://{}:{}/clear'.format(
  'localhost' if len(sys.argv) < 2 else sys.argv[1], 80))
res = requests.post('http://{}:{}/add_animation'.format(
  'localhost' if len(sys.argv) < 2 else sys.argv[1],
  80), data=data, headers={'Content-Type': 'application/json'})

#print(res.text)
