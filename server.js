const WebSocket = require('ws');
const { spawn } = require('child_process');

// Replace with your actual YouTube stream key
const YT_URL = `rtmps://a.rtmp.youtube.com/live2/fvgb-pzbe-4j7g-vej0-6g7q`;

// WebSocket server
const wss = new WebSocket.Server({ port: 8443 });
console.log("WebSocket server running on ws://localhost:8443");

// Start FFmpeg process
const ffmpeg = spawn('ffmpeg', [
    '-f', 'rawvideo',       // Input: raw video
    '-pix_fmt', 'rgb24',    // Pixel format from canvas
    '-s', '1280x720',       // Resolution
    '-r', '5',              // FPS
    '-i', 'pipe:0',         // Input from stdin
    '-c:v', 'libx264',      // Encode video
    '-preset', 'veryfast',
    '-pix_fmt', 'yuv420p',
    '-f', 'flv',            // RTMP format
    YT_URL
]);

ffmpeg.stderr.on('data', data => console.log('FFmpeg:', data.toString()));
ffmpeg.on('close', code => console.log('FFmpeg exited with code', code));
ffmpeg.on('error', err => console.error('FFmpeg error:', err));

// Handle incoming WebSocket connections
wss.on('connection', ws => {
    console.log("Client connected");

    ws.on('message', message => {
        // message is expected to be raw RGB24 frame
        if (!ffmpeg.stdin.destroyed) {
            ffmpeg.stdin.write(message);
        }
    });

    ws.on('close', () => console.log("Client disconnected"));
});
