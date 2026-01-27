import os
import time
import requests
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import ffmpeg

# ------------------ SETTINGS ------------------
WIDTH, HEIGHT = 1280, 720
FPS = 5

# Your YouTube stream key
YOUTUBE_STREAM_KEY = "abcd-efgh-ijkl-mnop"  # <-- Replace with your key
YOUTUBE_URL = f"rtmp://a.rtmp.youtube.com/live2/{YOUTUBE_STREAM_KEY}"

# Fonts
FONT_LARGE = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 30)
FONT_MED   = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 22)
FONT_SMALL = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)

# ------------------ ALERT PRIORITY ------------------
PRIORITY = {
    "Tornado Emergency": 100,
    "Tornado Warning": 95,
    "Severe Thunderstorm Warning": 80,
    "Flash Flood Warning": 75,
    "Tornado Watch": 60,
    "Severe Thunderstorm Watch": 50
}

# ------------------ START RTMP ------------------
def start_rtmp():
    print("🚀 Starting Y’allBot Live Stream to YouTube...")
    return (
        ffmpeg
        .input("pipe:", format="rawvideo", pix_fmt="rgb24",
               s=f"{WIDTH}x{HEIGHT}", framerate=FPS)
        .output(YOUTUBE_URL, format="flv",
                vcodec="libx264", pix_fmt="yuv420p",
                preset="veryfast", g=FPS*2)
        .overwrite_output()
        .run_async(pipe_stdin=True)
    )

# ------------------ FETCH NOAA ALERTS ------------------
def fetch_noaa_alerts():
    try:
        res = requests.get("https://api.weather.gov/alerts/active", timeout=8)
        data = res.json()
        alerts = []

        for f in data.get("features", []):
            props = f.get("properties", {})
            event = props.get("event")
            if event in PRIORITY:
                alerts.append({
                    "event": event,
                    "area": props.get("areaDesc", ""),
                    "severity": PRIORITY[event]
                })

        alerts.sort(key=lambda x: x["severity"], reverse=True)
        return alerts
    except:
        return []

# ------------------ DRAW FRAME ------------------
def draw_frame(alerts, ticker_x):
    frame = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
    pil = Image.fromarray(frame)
    draw = ImageDraw.Draw(pil)

    # Top title bar
    draw.rectangle((0, 0, WIDTH, 40), fill=(0, 0, 0))
    draw.text((10, 5), "Y’allBot 24/7 USA Weather Alerts (Ryan Hall style)",
              font=FONT_LARGE, fill=(255, 255, 255))

    # Top alert box (highest priority)
    if alerts:
        top = alerts[0]
        fill = (255, 0, 0) if "Tornado" in top["event"] else (255, 140, 0)
        draw.rectangle((0, 50, WIDTH, 100), fill=fill)
        draw.text((10, 55), f"{top['event']} — {top['area']}", font=FONT_MED, fill=(0, 0, 0))

    # Side panel for other alerts
    draw.rectangle((WIDTH-280, 110, WIDTH-10, 270), fill=(20, 20, 20))
    draw.text((WIDTH-270, 120), "Active Warnings", font=FONT_MED, fill=(255, 255, 255))
    y = 155
    for a in alerts[:6]:
        draw.text((WIDTH-270, y), a["event"], font=FONT_SMALL, fill=(255, 0, 0))
        y += 24

    # Scrolling ticker
    crawl = " | ".join([f"{a['event']} - {a['area']}" for a in alerts])
    draw.rectangle((0, HEIGHT-60, WIDTH, HEIGHT), fill=(0, 0, 0))
    draw.text((ticker_x, HEIGHT-45), crawl, font=FONT_MED, fill=(255, 0, 0))

    return np.array(pil), len(crawl) * 12

# ------------------ MAIN LOOP ------------------
def main():
    streamer = start_rtmp()
    ticker_x = WIDTH
    last_alert = 0
    alerts = []

    print("🚀 Y’allBot running. Press Ctrl+C to stop.")

    frame_id = 0
    while True:
        # Update alerts every 30 seconds
        if time.time() - last_alert > 30:
            alerts = fetch_noaa_alerts()
            last_alert = time.time()

        frame, crawl_width = draw_frame(alerts, ticker_x)
        ticker_x -= 5
        if ticker_x < -crawl_width:
            ticker_x = WIDTH

        try:
            streamer.stdin.write(frame.tobytes())
            frame_id += 1
        except BrokenPipeError:
            print("❌ Stream disconnected")
            break

        time.sleep(1 / FPS)

if __name__ == "__main__":
    main()
