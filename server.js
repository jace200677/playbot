const WebSocket = require('ws');
const { spawn } = require('child_process');
const wrtc = require('wrtc');

const wss = new WebSocket.Server({ port: 8443 });
console.log("WebSocket server running on port 8443");

// Replace with your actual YouTube RTMPS URL
const YT_URL = "rtmp://a.rtmp.youtube.com/live2/fvgb-pzbe-4j7g-vej0-6g7q";

wss.on('connection', ws => {
    let ffmpeg = spawn('ffmpeg', [
        '-f','rawvideo','-pix_fmt','yuv420p','-s','1280x720','-r','5','-i','pipe:0',
        '-c:v','libx264','-preset','veryfast','-f','flv',YT_URL
    ]);

    ffmpeg.stderr.on('data', data => console.log('FFmpeg:', data.toString()));

    ws.on('message', message => {
        // In production, connect WebRTC track to FFmpeg input
        // For simplicity, we assume raw frames are sent (requires proper H.264 encoder)
        ffmpeg.stdin.write(message);
    });

    ws.on('close', () => { ffmpeg.kill('SIGINT'); });
});
