import requests
import pyttsx3
import time
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import ffmpeg

# ---------------- YouTube RTMP ----------------
YOUTUBE_URL = "rtmp://a.rtmp.youtube.com/live2"
STREAM_KEY = "YOUR_YOUTUBE_STREAM_KEY"

# ---------------- TTS ----------------
engine = pyttsx3.init('espeak')
engine.setProperty("rate", 160)
engine.setProperty("volume", 1.0)

def speak_alert(text):
    print("🎙️ PLAYBOT:", text)
    engine.say(text)
    engine.runAndWait()

# ---------------- NOAA Alerts ----------------
def fetch_noaa_alerts():
    try:
        res = requests.get("https://api.weather.gov/alerts/active", timeout=10)
        data = res.json()
        alerts = []
        for feature in data.get("features", []):
            props = feature["properties"]
            if props.get("severity") in ["Severe","Extreme"]:
                alerts.append({
                    "event": props.get("event"),
                    "areas": props.get("areaDesc"),
                    "effective": props.get("effective"),
                })
        return alerts
    except:
        return []

# ---------------- Map Frame ----------------
def create_frame(alerts):
    img = np.zeros((720,1280,3), dtype=np.uint8)
    img[:] = (0,0,0)
    pil = Image.fromarray(img)
    draw = ImageDraw.Draw(pil)
    font = ImageFont.load_default()
    draw.text((10,10), "PlayBot 24/7 USA Weather Alerts", fill=(255,255,255), font=font)
    y = 40
    for a in alerts[:10]:
        draw.text((10,y), f"{a['event']} — {a['areas']}", fill=(255,0,0), font=font)
        y += 20
    return np.array(pil)

# ---------------- FFmpeg Stream ----------------
def start_ffmpeg():
    process = (
        ffmpeg
        .input('pipe:', format='rawvideo', pix_fmt='bgr24', s='1280x720', framerate=1)
        .output(f'{YOUTUBE_URL}/{STREAM_KEY}', format='flv', vcodec='libx264', pix_fmt='yuv420p', r=1)
        .overwrite_output()
        .run_async(pipe_stdin=True)
    )
    return process

# ---------------- Main Loop ----------------
def run_playbot():
    print("🤖 PlayBot 24/7 Streaming with Voice")
    ffmpeg_proc = start_ffmpeg()

    while True:
        alerts = fetch_noaa_alerts()
        for a in alerts[:5]:
            speak_alert(f"{a['event']} in {a['areas']}")

        frame = create_frame(alerts)
        ffmpeg_proc.stdin.write(frame.tobytes())
        time.sleep(60)

if __name__ == "__main__":
    run_playbot()
