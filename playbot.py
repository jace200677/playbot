import os
import time
import requests
import numpy as np
import subprocess
from PIL import Image, ImageDraw, ImageFont

# ==============================
# YouTube RTMP
# ==============================
YOUTUBE_URL = "rtmp://a.rtmp.youtube.com/live2"
STREAM_KEY = os.environ.get("YOUTUBE_STREAM_KEY")

if not STREAM_KEY:
    raise RuntimeError("Missing YOUTUBE_STREAM_KEY environment variable")

# ==============================
# Video Settings
# ==============================
WIDTH = 1280
HEIGHT = 720
FPS = 5
FRAME_TIME = 1 / FPS

# ==============================
# Fonts
# ==============================
def load_font(size):
    try:
        return ImageFont.truetype("DejaVuSans-Bold.ttf", size)
    except:
        return ImageFont.load_default()

FONT_TITLE = load_font(32)
FONT_TEXT = load_font(18)

# ==============================
# NOAA Alerts
# ==============================
def fetch_noaa_alerts():
    alerts = []
    try:
        r = requests.get(
            "https://api.weather.gov/alerts/active",
            headers={"User-Agent": "PlayBot Weather Stream"},
            timeout=10
        )
        data = r.json()

        for f in data.get("features", []):
            p = f["properties"]
            if p.get("severity") in ("Severe", "Extreme"):
                alerts.append({
                    "event": p.get("event", "Alert"),
                    "areas": p.get("areaDesc", ""),
                })

    except Exception as e:
        print("NOAA error:", e)

    return alerts[:6]

# ==============================
# Frame Builder
# ==============================
def build_frame(alerts):
    img = Image.new("RGB", (WIDTH, HEIGHT), (0, 0, 0))
    d = ImageDraw.Draw(img)

    # Title
    d.text((20, 15), "PlayBot 24/7 USA Weather Alerts", fill=(255,255,255), font=FONT_TITLE)

    # Bottom bar
    bar_h = 150
    d.rectangle((0, HEIGHT-bar_h, WIDTH, HEIGHT), fill=(30,30,30))

    y = HEIGHT - bar_h + 15
    if alerts:
        for a in alerts:
            text = f"⚠ {a['event']} — {a['areas']}"
            d.text((20, y), text, fill=(255,80,80), font=FONT_TEXT)
            y += 22
    else:
        d.text((20, y), "No Severe or Extreme Alerts", fill=(200,200,200), font=FONT_TEXT)

    return np.array(img)

# ==============================
# FFmpeg Pipe
# ==============================
def start_ffmpeg():
    cmd = [
        "ffmpeg",
        "-loglevel", "error",
        "-f", "rawvideo",
        "-pix_fmt", "rgb24",
        "-s", f"{WIDTH}x{HEIGHT}",
        "-r", str(FPS),
        "-i", "-",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-pix_fmt", "yuv420p",
        "-g", str(FPS * 2),
        "-f", "flv",
        f"{YOUTUBE_URL}/{STREAM_KEY}"
    ]
    return subprocess.Popen(cmd, stdin=subprocess.PIPE)

# ==============================
# Main Loop
# ==============================
def main():
    print("▶ PlayBot Live Weather Stream STARTED")
    ffmpeg = start_ffmpeg()
    last_fetch = 0
    alerts = []

    while True:
        now = time.time()

        if now - last_fetch > 30:
            alerts = fetch_noaa_alerts()
            last_fetch = now

        frame = build_frame(alerts)

        try:
            ffmpeg.stdin.write(frame.tobytes())
        except BrokenPipeError:
            print("FFmpeg crashed, restarting...")
            ffmpeg = start_ffmpeg()

        time.sleep(FRAME_TIME)

# ==============================
if __name__ == "__main__":
    main()
