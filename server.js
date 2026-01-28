const WebSocket = require('ws');
const { spawn } = require('child_process');

// Replace with your actual YouTube stream key
const YT_URL = `rtmps://a.rtmp.youtube.com/live2/fvgb-pzbe-4j7g-vej0-6g7q`;

// WebSocket server for clients to push frames
const wss = new WebSocket.Server({ port: 8443 });
console.log("WebSocket server running on port 8443");

// Function to start FFmpeg pushing to YouTube
function startFFmpeg() {
    const ffmpeg = spawn('ffmpeg', [
        '-f', 'rawvideo',       // Input format
        '-pix_fmt', 'rgb24',    // Pixel format from canvas
        '-s', '1280x720',       // Frame size
        '-r', '5',              // FPS
        '-i', 'pipe:0',         // Input from stdin
        '-c:v', 'libx264',      // Encode to H.264
        '-preset', 'veryfast',
        '-pix_fmt', 'yuv420p',
        '-f', 'flv',            // RTMP output format
        YT_URL
    ]);

    ffmpeg.stderr.on('data', data => console.log('FFmpeg:', data.toString()));
    ffmpeg.on('close', code => console.log('FFmpeg exited with code', code));
    return ffmpeg;
}

// Handle incoming WebSocket connections
wss.on('connection', ws => {
    console.log("Client connected");
    const ffmpeg = startFFmpeg();

    ws.on('message', message => {
        // Browser should send raw frame bytes (RGB24)
        ffmpeg.stdin.write(message);
    });

    ws.on('close', () => {
        console.log("Client disconnected");
        ffmpeg.kill('SIGINT');
    });
});
