let _stream:   MediaStream | null   = null;
let _interval: ReturnType<typeof setInterval> | null = null;
let _video:    HTMLVideoElement | null = null;
let _canvas:   HTMLCanvasElement | null = null;
 
const CAPTURE_INTERVAL_MS = 3000;
const API_ENDPOINT        = "/api/engagement/video";
 
 
export async function startWebcam(userId: string = "default"): Promise<void> {
  if (_interval) return;  // déjà démarré
 
  try {
    _stream = await navigator.mediaDevices.getUserMedia({
      video: { width: 320, height: 240, facingMode: "user" },
      audio: false,
    });
 
    _video           = document.createElement("video");
    _video.srcObject = _stream;
    _video.style.display = "none";
    document.body.appendChild(_video);
    await _video.play();
 
    _canvas        = document.createElement("canvas");
    _canvas.width  = 320;
    _canvas.height = 240;
 
    console.log("[Webcam] ✅ Started");
 
    _interval = setInterval(() => _captureAndSend(userId), CAPTURE_INTERVAL_MS);
    _captureAndSend(userId);
 
  } catch (err) {
    console.warn("[Webcam] ❌ Camera access denied:", (err as Error).message);
  }
}
 
 
export function stopWebcam(): void {
  if (_interval) {
    clearInterval(_interval);
    _interval = null;
  }
  if (_stream) {
    _stream.getTracks().forEach((t) => t.stop());
    _stream = null;
  }
  if (_video) {
    _video.remove();
    _video = null;
  }
  console.log("[Webcam] Stopped");
}
 
 
async function _captureAndSend(userId: string): Promise<void> {
  if (!_video || !_canvas || _video.readyState < 2) return;
 
  try {
    const ctx = _canvas.getContext("2d");
    if (!ctx) return;
 
    ctx.drawImage(_video, 0, 0, _canvas.width, _canvas.height);
    const base64 = _canvas.toDataURL("image/jpeg", 0.7).split(",")[1];
 
    const res = await fetch(API_ENDPOINT, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ frame: base64, user_id: userId }),
    });
 
    const data = await res.json();
    console.log(`[Webcam] 📸 video_score=${data.video_score} status=${data.status}`);
 
  } catch (err) {
    console.warn("[Webcam] Send error:", (err as Error).message);
  }
}
