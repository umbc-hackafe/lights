import time

STRAND_LENGTH = 50
ALL_BRIGHTNESS = 63
ALL_LIGHTS = list(range(STRAND_LENGTH))
FRAMERATE = 24
BRIGHTNESS_MAX = 255

def squash(segments):
    result = {}
    for segment in segments:
        result.update(segment)
    return result

def merge_animations(*animations):
    pass

def deserialize(obj):
    if "__type__" not in obj:
        print(obj)
        raise ValueError("Invalid data -- no '__type__'")

    kind = obj["__type__"]

    if kind == "Segment":
        return Segment.deserialize(obj)
    elif kind == "Frame":
        return Frame.deserialize(obj)
    elif kind == "Animation":
        return Animation.deserialize(obj)

def normalize_color(color):
    if isinstance(color, int):
        return [((color >> 16) & 0xFF) // 16,
                ((color >> 8) & 0xFF) // 16,
                (color & 0xFF) // 16]
    else:
        return color

# Takes a rendered frame to output, and a function of the form:
# put(id, brightness, r, g, b). Returns the time when the next frame
# should be rendered
def put_frame(rendered_frame, put):
    for light, state in rendered_frame["states"].items():
        put(light, state.get("brightness", 255), *(state.get("color", [0, 0, 0])))

    return time.time() + rendered_frame["duration"]

class FrameHolder:
    def __init__(self, frame=None):
        self.frame = frame

def put_animation(rendered_animation, put, last_frame=FrameHolder(), cutoff=False):
    end_time = rendered_animation["duration"] + time.time()
    while time.time() < end_time:
        for step in rendered_animation["steps"]:
            if step["type"] == "Animation":
                put_animation(step, put, last_frame, cutoff)
            elif step["type"] == "Frame":
                if last_frame.frame:
                    diff_frame(last_frame.frame, step, put)
                else:
                    put_frame(step, put)
                last_frame.frame = step
                time.sleep(step["duration"])
            if time.time() >= end_time and cutoff:
                break
    if time.time() < end_time:
        time.sleep(end_time - time.time())

class Segment:
    @classmethod
    def deserialize(cls, data):
        return Segment(data["lights"], data["color"], data["brightness"])

    def __init__(self, lights=ALL_LIGHTS, color=None, brightness=None):
        if isinstance(lights, int):
            lights = [lights]
        self.lights = list(lights)

        self.__state = {}

        if color is not None:
            self.__state["color"] = normalize_color(color)

        if brightness is not None:
            self.__state["brightness"] = brightness

    @property
    def brightness(self):
        return self.__state["brightness"]

    @brightness.setter
    def brightness(self, brightness):
        self.__state["brightness"] = brightness

    @property
    def color(self):
        return self.__state["color"]

    @color.setter
    def color(self, color):
        self.__state["color"] = color

    def render(self):
        return {l: self.__state for l in self.lights}

    def serialize(self):
        return {"__type__": "Segment",
                "lights": self.lights,
                "color": self.__state.get("color", None),
                "brightness": self.__state.get("brightness", None)}

BACKGROUND_OFF = Segment(color=0xFFFFFF, brightness=0)
BACKGROUND_BLACK = Segment(color=0x000000, brightness=255)
BACKGROUND_WHITE = Segment(color=0xFFFFFF, brightness=255)
BACKGROUND_RED = Segment(color=0xFF0000, brightness=255)
BACKGROUND_GREEN = Segment(color=0x00FF00, brightness=255)
BACKGROUND_BLUE = Segment(color=0x0000FF, brightness=255)

# Renders a frame only using the differences from previous frame
def diff_frame(a, b, put, background=BACKGROUND_BLACK):
    background = background.render()

    for light in a["states"].keys() - b["states"].keys():
        if light < STRAND_LENGTH:
            put(light, background[light]["brightness"],
                *background[light]["color"])

    for light, state in b["states"].items():
        if light not in a["states"] or a["states"][light] != state:
            put(light, state.get("brightness", 255), *state.get("color", [0,0,0]))

class Frame:
    @classmethod
    def deserialize(cls, data):
        return Frame(segments=[deserialize(seg) for seg in data["segments"]],
                     duration=data["duration"])

    def __init__(self, segments=[], duration=1):
        if isinstance(segments, Segment):
            segments = [segments]

        self.segments = segments
        self.duration = duration

    def insert_segment(self, segment, at=None):
        if at is None:
            at = len(self.segments)

        self.segments = self.segments[:at] + [segment] + self.segments[at:]

    def render(self):
        return {"type": "Frame",
                "states": squash((seg.render() for seg in self.segments)),
                "duration": self.duration}

    def serialize(self):
        return {"__type__": "Frame",
                "segments": [seg.serialize() for seg in self.segments],
                "duration": self.duration}

class Animation:
    @classmethod
    def deserialize(cls, data):
        return Animation(steps=[deserialize(s) for s in data["steps"]],
                         duration=data["duration"])

    def __init__(self, steps=[], duration=None):
        self.steps = steps

        self.duration = duration or sum((s.duration for s in steps))

    def render(self):
        return {"type": "Animation",
                "steps": [s.render() for s in self.steps],
                "duration": self.duration}

    def serialize(self):
        return {"__type__": "Animation",
                "steps": [s.serialize() for s in self.steps],
                "duration": self.duration}

class FadeIn(Animation):
    def __init__(self, duration=1, start=0, stop=BRIGHTNESS_MAX):
        steps = []
        for i in range(start, stop+1):
            steps.append(Frame(Segment(lights=ALL_BRIGHTNESS, brightness=i),
                               duration=(duration/abs(stop-start))))
        self.steps = steps
        self.duration = duration

class FadeOut(Animation):
    def __init__(self, duration=1, start=BRIGHTNESS_MAX, stop=0):
        steps = []
        for i in range(start, stop-1, -1):
            steps.append(Frame(Segment(lights=ALL_BRIGHTNESS, brightness=i),
                               duration=(duration/abs(start-stop))))
        self.steps = steps
        self.duration = duration
