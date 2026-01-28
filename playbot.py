import os
import time
import requests
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import ffmpeg
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# ------------------ STREAM SETTINGS ------------------
RTMP_URL = "rtmp://a.rtmp.youtube.com/live2"
STREAM_KEY = "fvgb-pzbe-4j7g-vej0-6g7q"  # Your stream key
WIDTH, HEIGHT = 1280, 720
FPS = 5

# ------------------ FONTS ------------------
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

# ------------------ START FFmpeg ------------------
def start_ffmpeg():
    video_input = ffmpeg.input(
        'pipe:',
        format='rawvideo',
        pix_fmt='rgb24',
        s=f'{WIDTH}x{HEIGHT}',
        framerate=FPS
    )

    audio_input = ffmpeg.input(
        'anullsrc=r=44100:cl=stereo',
        f='lavfi'
    )

    process = ffmpeg.output(
        video_input,
        audio_input,
        f'{RTMP_URL}/{STREAM_KEY}',
        format='flv',
        vcodec='libx264',
        pix_fmt='yuv420p',
        preset='veryfast',
        acodec='aac',
        audio_bitrate='128k'
    ).overwrite_output().run_async(pipe_stdin=True)

    return process

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

# ------------------ INIT HEADLESS CHROME ------------------
def init_map():
    options = Options()
    options.headless = False
    options.add_argument("--window-size=1280,720")  # Match your video frame size
    driver = webdriver.Chrome(options=options)

    # Load map from GitHub Pages
    driver.get("https://jace200677.github.io/playbot/map.html")
    time.sleep(2)  # Allow map tiles to load

    return driver

def update_map(driver, alerts):
    alerts_js = [{"event": a["event"], "area": a["area"]} for a in alerts]
    driver.execute_script(f"drawAlerts({alerts_js})")
    time.sleep(0.5)
    screenshot = driver.get_screenshot_as_png()
    img = Image.open(io.BytesIO(screenshot)).resize((650, 380))
    return img

# ------------------ DRAW FRAME ------------------
import io
def draw_frame(alerts, ticker_x, map_img=None):
    frame = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
    pil = Image.fromarray(frame)
    draw = ImageDraw.Draw(pil)

    # Title
    draw.rectangle((0,0,WIDTH,40), fill=(0,0,0))
    draw.text((10,5), "PlayBot 24/7 USA Weather Alerts", font=FONT_LARGE, fill=(255,255,255))

    # Top alert
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
        draw.text((WIDTH-270,y), a["event"], font=FONT_SMALL, fill=(255,0,0))
        y += 24

    # Map
    if map_img:
        pil.paste(map_img, (50,120))

    # Ticker
    crawl = " | ".join([f"{a['event']} - {a['area']}" for a in alerts])
    draw.rectangle((0,HEIGHT-60,WIDTH,HEIGHT), fill=(0,0,0))
    draw.text((ticker_x, HEIGHT-45), crawl, font=FONT_MED, fill=(255,0,0))

    return np.array(pil), len(crawl)*12

# ------------------ MAIN LOOP ------------------
def main():
    print("🚀 Starting PlayBot Live Stream")
    streamer = start_ffmpeg()
    driver = init_map()
    ticker_x = WIDTH
    last_alert = 0
    alerts = []
    map_img = None

    while True:
        if time.time() - last_alert > 30:
            alerts = fetch_noaa_alerts()
            last_alert = time.time()
            map_img = update_map(driver, alerts)

        frame, crawl_width = draw_frame(alerts, ticker_x, map_img)
        ticker_x -= 5
        if ticker_x < -crawl_width:
            ticker_x = WIDTH

        try:
            streamer.stdin.write(frame.tobytes())
        except BrokenPipeError:
            print("🔴 Stream disconnected")
            break

        time.sleep(1.0 / FPS)

if __name__ == "__main__":
    main()
