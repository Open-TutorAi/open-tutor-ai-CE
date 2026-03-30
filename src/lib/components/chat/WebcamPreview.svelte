<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  let stream: MediaStream | null = null;
  let videoEl: HTMLVideoElement;
  let canvasEl: HTMLCanvasElement;
  let score: number = 0.5;
  let level: string = 'medium';
  let interval: ReturnType<typeof setInterval>;
  $: color = level === 'low' ? '#ef4444' : level === 'high' ? '#22c55e' : '#f59e0b';

  onMount(async () => {
    try {
      stream = await navigator.mediaDevices.getUserMedia({ video: { width: 320, height: 240 }, audio: false });
      videoEl.srcObject = stream;
      await videoEl.play();
      interval = setInterval(capture, 3000);
      setTimeout(capture, 1000);
    } catch(e) { console.warn('Camera:', e); }
  });

  onDestroy(() => {
    clearInterval(interval);
    stream?.getTracks().forEach(t => t.stop());
  });

  async function capture() {
    if (!videoEl || !canvasEl || videoEl.readyState < 2) return;
    const ctx = canvasEl.getContext('2d');
    if (!ctx) return;
    ctx.drawImage(videoEl, 0, 0, 320, 240);
    const base64 = canvasEl.toDataURL('image/jpeg', 0.7).split(',')[1];
    try {
      const res = await fetch('http://localhost:8080/api/engagement/video', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ frame: base64, user_id: 'default' })
      });
      const data = await res.json();
      if (data.video_score !== null) {
        score = data.video_score;
        level = score < 0.5 ? 'low' : score >= 0.7 ? 'high' : 'medium';
      }
    } catch(e) {}
  }
</script>

<div style="position:fixed;bottom:16px;right:16px;z-index:9999;background:#1a1a2e;border-radius:12px;padding:8px;box-shadow:0 4px 20px rgba(0,0,0,0.5);">
  <video bind:this={videoEl} width="160" height="120" style="border-radius:8px;display:block;" muted playsinline></video>
  <canvas bind:this={canvasEl} width="320" height="240" style="display:none;"></canvas>
  <div style="margin-top:6px;text-align:center;font-family:monospace;font-size:13px;font-weight:bold;color:{color};">● {level.toUpperCase()}</div>
  <div style="text-align:center;font-size:11px;color:#aaa;">score: {score}</div>
</div>