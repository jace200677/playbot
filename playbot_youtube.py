import requests
import time
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import ffmpeg

# ---------------- YouTube RTMP ----------------
YOUTUBE_URL = "rtmp://a.rtmp.youtube.com/live2"
STREAM_KEY = "8z2g-s4ar-t1p8-9ab3-f90f"  # Replace with your key

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

# ---------------- Map Frame with Bottom Text ----------------
def create_frame(alerts):
    # Black background
    img = np.zeros((720,1280,3), dtype=np.uint8)
    pil = Image.fromarray(img)
    draw = ImageDraw.Draw(pil)
    font = ImageFont.load_default()

    # Draw a bottom text box
    box_height = 120
    draw.rectangle([0, 720-box_height, 1280, 720], fill=(30,30,30,200))

    # Add alert texts at the bottom
    y = 720 - box_height + 10
    for a in alerts[:5]:  # show up to 5 alerts
        text = f"{a['event']} — {a['areas']}"
        draw.text((10, y), text, fill=(255,0,0), font=font)
        y += 20

    # Title at the top
    draw.text((10,10), "PlayBot 24/7 USA Weather Alerts", fill=(255,255,255), font=font)

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
    print("🤖 PlayBot 24/7 Map + Alerts Stream")
    ffmpeg_proc = start_ffmpeg()

    while True:
        alerts = fetch_noaa_alerts()
        frame = create_frame(alerts)
        ffmpeg_proc.stdin.write(frame.tobytes())
        time.sleep(60)  # update every minute

if __name__ == "__main__":
    run_playbot()
