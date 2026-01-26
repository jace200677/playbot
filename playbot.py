import os, time, json
import requests
import numpy as np
import ffmpeg
from PIL import Image, ImageDraw, ImageFont
import cv2
from shapely.geometry import shape, Point
import matplotlib.path as mplPath

# ---- STREAM SETTINGS ----
RTMP = "rtmp://a.rtmp.youtube.com/live2"
KEY = os.environ["YOUTUBE_STREAM_KEY"]  # set this in environment
WIDTH, HEIGHT = 1280, 720
FPS = 5

# ---- FONT ----
FONT_LARGE = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 30)
FONT_MED = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 22)
FONT_SMALL = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)

# ---- ALERT PRIORITY ----
PRIORITY = {
    "Tornado Emergency": 100,
    "Tornado Warning": 95,
    "Severe Thunderstorm Warning": 80,
    "Flash Flood Warning": 75,
    "Tornado Watch": 60,
    "Severe Thunderstorm Watch": 50
}

# ---- RTMP PROCESS ----
def start_ffmpeg():
    return (
        ffmpeg
        .input("pipe:", format="rawvideo", pix_fmt="rgb24", s=f"{WIDTH}x{HEIGHT}", framerate=FPS)
        .output(f"{RTMP}/{KEY}", format="flv", vcodec="libx264", pix_fmt="yuv420p", preset="veryfast")
        .run_async(pipe_stdin=True)
    )

# ---- FETCH NOAA ALERTS ----
def fetch_noaa_alerts():
    try:
        r = requests.get("https://api.weather.gov/alerts/active", timeout=8).json()
        alerts = []
        for f in r.get("features", []):
            p = f["properties"]
            event = p.get("event")
            if event in PRIORITY:
                alerts.append({
                    "event": event,
                    "area": p.get("areaDesc"),
                    "severity": PRIORITY[event],
                    "ends": p.get("ends"),
                    "sent": p.get("sent")
                })
        return sorted(alerts, key=lambda x: x["severity"], reverse=True)
    except:
        return []

# ---- DRAW FRAME ----
def draw_frame(background_frame, alerts, ticker_x):
    pil = Image.fromarray(background_frame)
    draw = ImageDraw.Draw(pil)

    # Title
    draw.rectangle((0,0,WIDTH,40), fill=(0,0,0))
    draw.text((10,5), "USA 24/7 Severe Weather Monitor", font=FONT_LARGE, fill=(255,255,255))

    # Top alert box (highest priority)
    if alerts:
        top = alerts[0]
        fill = (255,0,0) if "Tornado" in top["event"] else (255,140,0)
        draw.rectangle((0,50,WIDTH,100), fill=fill)
        draw.text((10,55), f"{top['event']} — {top['area']}", font=FONT_MED, fill=(0,0,0))

    # Side panel
    draw.rectangle((WIDTH-280,110,WIDTH-10,270), fill=(20,20,20))
    draw.text((WIDTH-270,120), "Active Warnings", font=FONT_MED, fill=(255,255,255))
    y=155
    for a in alerts[:6]:
        draw.text((WIDTH-270,y), f"{a['event']}", font=FONT_SMALL, fill=(255,0,0))
        y+=24

    # Ticker
    crawl = " | ".join([f"{a['event']} - {a['area']}" for a in alerts])
    draw.rectangle((0,HEIGHT-60,WIDTH,HEIGHT), fill=(0,0,0))
    draw.text((ticker_x,HEIGHT-45), crawl, font=FONT_MED, fill=(255,0,0))

    return np.array(pil), len(crawl)*12

# ---- BACKGROUND (Video or Radar) ----
def get_base_frame(cap):
    ret, frame = cap.read()
    if not ret:
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        ret, frame = cap.read()
    frame = cv2.resize(frame, (WIDTH,HEIGHT))
    return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

def main():
    cap = cv2.VideoCapture("background.mp4")  # looped background
    streamer = start_ffmpeg()
    ticker_x = WIDTH

    last_alert = 0
    alerts = []

    while True:
        frame_rgb = get_base_frame(cap)

        # update alerts periodically
        if time.time() - last_alert > 30:
            alerts = fetch_noaa_alerts()
            last_alert = time.time()

        out_frame, crawl_width = draw_frame(frame_rgb, alerts, ticker_x)
        ticker_x -= 5
        if ticker_x < -crawl_width:
            ticker_x = WIDTH

        try:
            streamer.stdin.write(out_frame.tobytes())
        except:
            break

        time.sleep(1.0 / FPS)

if __name__ == "__main__":
    main()
