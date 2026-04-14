<script lang="ts">
  import { onMount, onDestroy } from 'svelte';

  let stream: MediaStream | null = null;
  let videoEl: HTMLVideoElement;
  let canvasEl: HTMLCanvasElement;

  let score: number = 0.5;
  let level: string = 'medium';
  let status: string = 'loading';

  let interval: ReturnType<typeof setInterval>;
  let history: number[] = [];

  $: color =
    level === 'low'
      ? '#ef4444'
      : level === 'high'
      ? '#22c55e'
      : '#f59e0b';

  // ----------------------------
  // Smooth score 
  // ----------------------------
  function smooth(newScore: number) {
    history.push(newScore);
    if (history.length > 5) history.shift();
    return history.reduce((a, b) => a + b, 0) / history.length;
  }

  // ----------------------------
  // Lifecycle
  // ----------------------------
  onMount(async () => {
    try {
      stream = await navigator.mediaDevices.getUserMedia({
        video: { width: 320, height: 240 },
        audio: false
      });

      videoEl.srcObject = stream;
      await videoEl.play();

      status = 'active';

      // capture every 1.5 sec (better UX)
      interval = setInterval(capture, 1500);

      // first fast capture
      setTimeout(capture, 800);

    } catch (e) {
      console.warn('Camera error:', e);
      status = 'error';
    }
  });

  onDestroy(() => {
    clearInterval(interval);
    stream?.getTracks().forEach(t => t.stop());
  });

  // ----------------------------
  // Capture + API call
  // ----------------------------
  async function capture() {
    if (!videoEl || !canvasEl || videoEl.readyState < 2) return;

    const ctx = canvasEl.getContext('2d');
    if (!ctx) return;

    ctx.drawImage(videoEl, 0, 0, 320, 240);

    const base64 = canvasEl
      .toDataURL('image/jpeg', 0.7)
      .split(',')[1];

    try {
      const res = await fetch(
        'http://localhost:8080/api/engagement/video',
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            frame: base64,
            user_id: 'default'
          })
        }
      );

      const data = await res.json();

      if (
        data.video_score !== null &&
        data.video_score !== undefined
      ) {
        score = smooth(data.video_score);
      } else {
        // fallback if no face detected
        score = 0.3;
      }

      // consistent thresholds
      level =
        score < 0.4
          ? 'low'
          : score < 0.75
          ? 'medium'
          : 'high';

    } catch (e) {
      console.warn('API error:', e);
      status = 'error';
    }
  }
</script>

<!-- ----------------------------
 UI
----------------------------- -->

<div
  style="
    position:fixed;
    bottom:16px;
    right:16px;
    z-index:9999;
    background:#1a1a2e;
    border-radius:14px;
    padding:10px;
    box-shadow:0 6px 25px rgba(0,0,0,0.6);
    width:170px;
  "
>
  <!-- VIDEO -->
  <video
    bind:this={videoEl}
    width="160"
    height="120"
    style="border-radius:8px;display:block;"
    muted
    playsinline
  ></video>

  <canvas
    bind:this={canvasEl}
    width="320"
    height="240"
    style="display:none;"
  ></canvas>

  <!-- STATUS -->
  <div
    style="
      text-align:center;
      font-size:10px;
      color:#888;
      margin-top:4px;
    "
  >
    {status}
  </div>

  <!-- LEVEL -->
  <div
    style="
      margin-top:4px;
      text-align:center;
      font-family:monospace;
      font-size:13px;
      font-weight:bold;
      color:{color};
    "
  >
    ● {level.toUpperCase()}
  </div>

  <!-- SCORE -->
  <div
    style="
      text-align:center;
      font-size:11px;
      color:#aaa;
    "
  >
    score: {score.toFixed(3)}
  </div>

  <!-- PROGRESS BAR -->
  <div
    style="
      margin-top:6px;
      height:4px;
      background:#333;
      border-radius:4px;
      overflow:hidden;
    "
  >
    <div
      style="
        height:100%;
        width:{score * 100}%;
        background:{color};
        transition:width 0.3s ease;
      "
    ></div>
  </div>
</div>