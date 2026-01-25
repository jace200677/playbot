import requests
import pyttsx3
import time
from datetime import datetime
import numpy as np
import cv2
import ffmpeg
from PIL import Image, ImageDraw, ImageFont
import subprocess

# ---------------- YouTube Stream Settings ----------------
YOUTUBE_STREAM_URL = "rtmp://a.rtmp.youtube.com/live2"
YOUTUBE_STREAM_KEY = "p9yk-71aq-0tpx-ga26-623d"  # Replace with your key

# ---------------- TTS ----------------
engine = pyttsx3.init()
engine.setProperty("rate", 160)
engine.setProperty("volume", 1.0)

def speak_alert(text):
    print("🎙️ PLAYBOT:", text)
    engine.say(text)
    engine.runAndWait()

# ---------------- Fetch NOAA Alerts ----------------
def fetch_noaa_alerts():
    url = "https://api.weather.gov/alerts/active"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        alerts = []
        for feature in data.get("features", []):
            props = feature["properties"]
            if props.get("severity") in ["Severe", "Extreme"]:
                alerts.append({
                    "event": props.get("event"),
                    "areas": props.get("areaDesc"),
                    "effective": props.get("effective"),
                    "expires": props.get("expires"),
                })
        return alerts
    except Exception as e:
        print("Error fetching NOAA alerts:", e)
        return []

# ---------------- Generate Map Frame ----------------
def create_map_frame(alerts):
    # White background
    img = np.zeros((720,1280,3), dtype=np.uint8)
    img[:] = (30,30,30)  # dark background

    # Draw title
    pil_img = Image.fromarray(img)
    draw = ImageDraw.Draw(pil_img)
    font = ImageFont.load_default()
    draw.text((10,10), "PlayBot 24/7 USA Weather Alerts", fill=(255,255,255), font=font)

    # Draw alerts
    y = 40
    for alert in alerts[:10]:  # show top 10 alerts
        text = f"{alert['event']} — {alert['areas']}"
        draw.text((10, y), text, fill=(255,0,0), font=font)
        y += 20

    return np.array(pil_img)

# ---------------- Stream to YouTube ----------------
def stream_to_youtube():
    process = (
        ffmpeg
        .input('pipe:', format='rawvideo', pix_fmt='bgr24', s='1280x720', framerate=1)
        .output(f'{YOUTUBE_STREAM_URL}/{YOUTUBE_STREAM_KEY}', format='flv', vcodec='libx264', pix_fmt='yuv420p', r=1)
        .overwrite_output()
        .run_async(pipe_stdin=True)
    )
    return process

# ---------------- Main Loop ----------------
def run_playbot():
    print("🤖 PlayBot 24/7 YouTube Stream Starting...")
    stream_proc = stream_to_youtube()

    while True:
        alerts = fetch_noaa_alerts()

        if alerts:
            for alert in alerts[:5]:  # speak top 5 alerts
                message = f"{alert['event']} for {alert['areas']}"
                speak_alert(message)

        frame = create_map_frame(alerts)
        # Send frame to ffmpeg stdin
        stream_proc.stdin.write(frame.tobytes())

        time.sleep(60)  # update every minute

if __name__ == "__main__":
    run_playbot()
