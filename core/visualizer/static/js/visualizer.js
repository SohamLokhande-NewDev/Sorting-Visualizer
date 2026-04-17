/* ============================================================
   VISUALIZER.JS — Animation engine + chart
   ============================================================ */

function initVisualizer(imageId) {
  let sortData   = null;
  let currentAlgo = 'bubble';
  let frames      = [];
  let frameIndex  = 0;
  let playing     = false;
  let animTimer   = null;
  let animStartTime = 0;
  let timingData = {}; // Store { algo: [{ speed: val, times: [ms values] }] }

  const ALGO_META = {
    bubble:    { name: 'Bubble Sort',    complexity: 'Avg: O(n²) · Space: O(1)' },
    insertion: { name: 'Insertion Sort', complexity: 'Avg: O(n²) · Space: O(1)' },
    quick:     { name: 'Quick Sort',     complexity: 'Avg: O(n log n) · Space: O(log n)' },
    merge:     { name: 'Merge Sort',     complexity: 'Avg: O(n log n) · Space: O(n)' },
  };

  const ALGO_COLORS = { bubble: '#38bdf8', insertion: '#818cf8', quick: '#34d399', merge: '#fb923c' };

  /* ── FETCH DATA ─────────────────────────────────── */
  fetch('/sort/' + imageId + '/')
    .then(r => r.json())
    .then(data => {
      sortData = data;
      loadAlgo('bubble');
      renderChart(data.stats);
    })
    .catch(err => {
      document.getElementById('slices-stage').innerHTML =
        '<div style="color:var(--sky);margin:auto;font-size:0.85rem;">Failed to load data. Check the API.</div>';
      console.error('Sort API error:', err);
    });

  /* ── LOAD ALGORITHM ─────────────────────────────── */
  function loadAlgo(algo) {
    currentAlgo = algo;
    stopAnimation();
    frames     = sortData[algo] || [];
    frameIndex = 0;

    document.querySelectorAll('.algo-btn[data-algo]').forEach(b => {
      b.classList.toggle('active', b.dataset.algo === algo);
    });
    document.getElementById('algo-name').textContent       = ALGO_META[algo].name;
    document.getElementById('algo-complexity').textContent = ALGO_META[algo].complexity;
    document.getElementById('stat-frames').textContent     = frames.length;
    document.getElementById('stat-current').textContent    = 1;
    document.getElementById('stat-status').textContent     = 'Ready';
    document.getElementById('stat-slices').textContent     = sortData.initial ? sortData.initial.length : '—';
    document.getElementById('frame-counter').textContent   = 'Frame 1 / ' + frames.length;
    document.getElementById('progress-fill').style.width  = '0%';

    // Always show the combined timing chart (persists across all algorithms)
    renderAllTimingCharts();

    if (frames.length > 0) renderFrame(frames[0]);
  }

  /* ── RENDER FRAME ───────────────────────────────── */
  function renderFrame(frame) {
    const stage = document.getElementById('slices-stage');
    stage.innerHTML = '';

    const order   = frame.order || frame;
    const swaps   = frame.swapping  || [];
    const compares= frame.comparing || [];

    order.forEach((id, idx) => {
      const img = document.createElement('img');
      img.className = 'slice-img';
      img.src = sortData.paths[id] || '';
      img.alt = 'slice-' + id;
      if (swaps.includes(id))    img.classList.add('swapping');
      if (compares.includes(id)) img.classList.add('comparing');
      stage.appendChild(img);
    });
  }

  /* ── ANIMATION ──────────────────────────────────── */
  function stepForward() {
    if (frameIndex >= frames.length - 1) {
      return;
    }
    frameIndex++;
    renderFrame(frames[frameIndex]);
    updateUI();
  }

  function getDelay() {
    const raw = parseInt(document.getElementById('speed-ctrl').value);
    return 850 - raw; // invert: high slider = fast
  }

  function startAnimation() {
    playing = true;
    animStartTime = performance.now();
    let frameTimings = [0]; // Frame 0 starts at time 0
    document.getElementById('btn-play').textContent = '⏸';
    document.getElementById('btn-play').classList.add('playing');
    document.getElementById('stat-status').textContent = 'Running';
    
    function loop() {
      stepForward();
      const elapsed = performance.now() - animStartTime;
      frameTimings.push(elapsed);
      
      // Update chart in real-time showing all algorithms
      renderAllTimingChartsLive(frameTimings, frames.length);
      
      if (frameIndex >= frames.length - 1) {
        stopAnimation();
        document.getElementById('stat-status').textContent = 'Completed';
        // Store timing data
        const currentSpeed = parseInt(document.getElementById('speed-ctrl').value);
        if (!timingData[currentAlgo]) timingData[currentAlgo] = [];
        const timingRun = { speed: currentSpeed, times: [...frameTimings] }; // Create a copy
        timingData[currentAlgo].push(timingRun);
        // Save to localStorage for report page
        const dataToSave = {
          imageId: imageId,
          timingData: timingData,
          timestamp: new Date().toISOString()
        };
        localStorage.setItem('visualizerData_' + imageId, JSON.stringify(dataToSave));
        console.log('Saved timing data to localStorage:', dataToSave);
        return;
      }
      if (playing) {
        animTimer = setTimeout(loop, getDelay());
      }
    }
    loop();
  }

  function stopAnimation() {
    playing = false;
    clearTimeout(animTimer);
    document.getElementById('btn-play').textContent = '▶';
    document.getElementById('btn-play').classList.remove('playing');
    if (document.getElementById('stat-status').textContent === 'Running')
      document.getElementById('stat-status').textContent = 'Paused';
  }

  function updateUI() {
    const pct = frames.length > 1 ? (frameIndex / (frames.length - 1)) * 100 : 100;
    document.getElementById('progress-fill').style.width = pct.toFixed(1) + '%';
    document.getElementById('stat-current').textContent   = frameIndex + 1;
    document.getElementById('frame-counter').textContent  = 'Frame ' + (frameIndex + 1) + ' / ' + frames.length;
  }

  /* ── CONTROLS ───────────────────────────────────── */
  document.getElementById('btn-play').addEventListener('click', () => {
    if (playing) stopAnimation();
    else startAnimation();
  });

  document.getElementById('btn-reset').addEventListener('click', () => {
    stopAnimation();
    frameIndex = 0;
    if (frames.length > 0) renderFrame(frames[0]);
    updateUI();
    document.getElementById('stat-status').textContent = 'Ready';
    document.getElementById('progress-fill').style.width = '0%';
  });

  document.querySelectorAll('.algo-btn[data-algo]').forEach(btn => {
    btn.addEventListener('click', () => loadAlgo(btn.dataset.algo));
  });

  /* ── ALL TIMING CHARTS LIVE (Real-time, all algorithms) ─── */
  function renderAllTimingChartsLive(currentFrameTimings, totalFrames) {
    const canvas = document.getElementById('time-chart');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    const W = canvas.offsetWidth || 600;
    const H = canvas.offsetHeight || 220;
    canvas.width = W * devicePixelRatio;
    canvas.height = H * devicePixelRatio;
    ctx.scale(devicePixelRatio, devicePixelRatio);

    // Calculate max time across all algorithms
    let globalMaxTime = Math.max(...currentFrameTimings, 100) * 1.1;
    for (let algo in timingData) {
      for (let run of timingData[algo]) {
        globalMaxTime = Math.max(globalMaxTime, Math.max(...run.times) * 1.1);
      }
    }

    const maxFrames = totalFrames;
    const PAD_L = 50, PAD_R = 20, PAD_T = 20, PAD_B = 40;
    const chartW = W - PAD_L - PAD_R;
    const chartH = H - PAD_T - PAD_B;

    const isLight = document.body.classList.contains('light');
    const gridColor = isLight ? 'rgba(0,0,0,0.07)' : 'rgba(255,255,255,0.05)';
    const textColor = isLight ? 'rgba(0,0,0,0.45)' : 'rgba(255,255,255,0.35)';
    const axisColor = isLight ? 'rgba(0,0,0,0.15)' : 'rgba(255,255,255,0.1)';

    ctx.clearRect(0, 0, W, H);

    // Grid lines (horizontal)
    ctx.strokeStyle = gridColor;
    ctx.lineWidth = 0.5;
    for (let i = 0; i <= 4; i++) {
      const y = PAD_T + chartH - (i / 4) * chartH;
      ctx.beginPath();
      ctx.moveTo(PAD_L, y);
      ctx.lineTo(PAD_L + chartW, y);
      ctx.stroke();
      ctx.fillStyle = textColor;
      ctx.font = '10px sans-serif';
      ctx.textAlign = 'right';
      const timeVal = (globalMaxTime * i / 4 / 1000).toFixed(1);
      ctx.fillText(timeVal + 's', PAD_L - 6, y + 3);
    }

    // Draw all completed runs
    const algos = ['bubble', 'insertion', 'quick', 'merge'];
    
    algos.forEach(algo => {
      if (timingData[algo]) {
        timingData[algo].forEach((timing, idx) => {
          const color = ALGO_COLORS[algo];
          const times = timing.times;
          
          ctx.strokeStyle = color;
          ctx.lineWidth = 1.5;
          ctx.globalAlpha = 0.6;
          ctx.beginPath();
          let isFirst = true;
          times.forEach((t, frameNum) => {
            const x = PAD_L + (frameNum / (maxFrames - 1 || 1)) * chartW;
            const y = PAD_T + chartH - (t / globalMaxTime) * chartH;
            if (isFirst) {
              ctx.moveTo(x, y);
              isFirst = false;
            } else {
              ctx.lineTo(x, y);
            }
          });
          ctx.stroke();

          // Draw dots
          ctx.fillStyle = color;
          times.forEach((t, frameNum) => {
            const x = PAD_L + (frameNum / (maxFrames - 1 || 1)) * chartW;
            const y = PAD_T + chartH - (t / globalMaxTime) * chartH;
            ctx.beginPath();
            ctx.arc(x, y, 1.5, 0, Math.PI * 2);
            ctx.fill();
          });
          ctx.globalAlpha = 1;
        });
      }
    });

    // Draw current running line (brighter)
    const currentColor = ALGO_COLORS[currentAlgo];
    ctx.strokeStyle = currentColor;
    ctx.lineWidth = 2.5;
    ctx.globalAlpha = 1;
    ctx.beginPath();
    let isFirst = true;
    currentFrameTimings.forEach((t, frameNum) => {
      const x = PAD_L + (frameNum / (maxFrames - 1 || 1)) * chartW;
      const y = PAD_T + chartH - (t / globalMaxTime) * chartH;
      if (isFirst) {
        ctx.moveTo(x, y);
        isFirst = false;
      } else {
        ctx.lineTo(x, y);
      }
    });
    ctx.stroke();

    // Draw dots at current position
    ctx.fillStyle = currentColor;
    currentFrameTimings.forEach((t, frameNum) => {
      const x = PAD_L + (frameNum / (maxFrames - 1 || 1)) * chartW;
      const y = PAD_T + chartH - (t / globalMaxTime) * chartH;
      ctx.beginPath();
      ctx.arc(x, y, 2.5, 0, Math.PI * 2);
      ctx.fill();
    });

    // Highlight current position
    const currentX = PAD_L + ((currentFrameTimings.length - 1) / (maxFrames - 1 || 1)) * chartW;
    const currentY = PAD_T + chartH - (currentFrameTimings[currentFrameTimings.length - 1] / globalMaxTime) * chartH;
    ctx.strokeStyle = currentColor;
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.arc(currentX, currentY, 4, 0, Math.PI * 2);
    ctx.stroke();

    // Axis
    ctx.strokeStyle = axisColor;
    ctx.lineWidth = 0.5;
    ctx.beginPath();
    ctx.moveTo(PAD_L, PAD_T);
    ctx.lineTo(PAD_L, PAD_T + chartH);
    ctx.lineTo(PAD_L + chartW, PAD_T + chartH);
    ctx.stroke();

    // X-axis label
    ctx.fillStyle = textColor;
    ctx.font = '11px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('Frames', PAD_L + chartW / 2, PAD_T + chartH + 32);

    // Y-axis label
    ctx.save();
    ctx.translate(8, PAD_T + chartH / 2);
    ctx.rotate(-Math.PI / 2);
    ctx.fillText('Time (seconds)', 0, 0);
    ctx.restore();
  }

  /* ── ALL TIMING CHARTS (Static view of all accumulated data) ─ */
  function renderAllTimingCharts() {
    const canvas = document.getElementById('time-chart');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    const W = canvas.offsetWidth || 600;
    const H = canvas.offsetHeight || 220;
    canvas.width = W * devicePixelRatio;
    canvas.height = H * devicePixelRatio;
    ctx.scale(devicePixelRatio, devicePixelRatio);

    // Calculate max time across all algorithms
    let globalMaxTime = 100;
    for (let algo in timingData) {
      for (let run of timingData[algo]) {
        globalMaxTime = Math.max(globalMaxTime, Math.max(...run.times) * 1.1);
      }
    }

    const maxFrames = Math.max(
      ...(Object.values(frames) || [100]).map(f => Array.isArray(f) ? f.length : 0),
      100
    );

    const PAD_L = 50, PAD_R = 20, PAD_T = 20, PAD_B = 40;
    const chartW = W - PAD_L - PAD_R;
    const chartH = H - PAD_T - PAD_B;

    const isLight = document.body.classList.contains('light');
    const gridColor = isLight ? 'rgba(0,0,0,0.07)' : 'rgba(255,255,255,0.05)';
    const textColor = isLight ? 'rgba(0,0,0,0.45)' : 'rgba(255,255,255,0.35)';
    const axisColor = isLight ? 'rgba(0,0,0,0.15)' : 'rgba(255,255,255,0.1)';

    ctx.clearRect(0, 0, W, H);

    // Grid lines (horizontal)
    ctx.strokeStyle = gridColor;
    ctx.lineWidth = 0.5;
    for (let i = 0; i <= 4; i++) {
      const y = PAD_T + chartH - (i / 4) * chartH;
      ctx.beginPath();
      ctx.moveTo(PAD_L, y);
      ctx.lineTo(PAD_L + chartW, y);
      ctx.stroke();
      ctx.fillStyle = textColor;
      ctx.font = '10px sans-serif';
      ctx.textAlign = 'right';
      const timeVal = (globalMaxTime * i / 4 / 1000).toFixed(1);
      ctx.fillText(timeVal + 's', PAD_L - 6, y + 3);
    }

    // Draw all runs
    const algos = ['bubble', 'insertion', 'quick', 'merge'];
    
    algos.forEach(algo => {
      if (timingData[algo]) {
        timingData[algo].forEach((timing, idx) => {
          const color = ALGO_COLORS[algo];
          const times = timing.times;
          
          ctx.strokeStyle = color;
          ctx.lineWidth = 2;
          ctx.beginPath();
          let isFirst = true;
          times.forEach((t, frameNum) => {
            const x = PAD_L + (frameNum / (maxFrames - 1 || 1)) * chartW;
            const y = PAD_T + chartH - (t / globalMaxTime) * chartH;
            if (isFirst) {
              ctx.moveTo(x, y);
              isFirst = false;
            } else {
              ctx.lineTo(x, y);
            }
          });
          ctx.stroke();

          // Draw dots
          ctx.fillStyle = color;
          times.forEach((t, frameNum) => {
            const x = PAD_L + (frameNum / (maxFrames - 1 || 1)) * chartW;
            const y = PAD_T + chartH - (t / globalMaxTime) * chartH;
            ctx.beginPath();
            ctx.arc(x, y, 2, 0, Math.PI * 2);
            ctx.fill();
          });
        });
      }
    });

    // Axis
    ctx.strokeStyle = axisColor;
    ctx.lineWidth = 0.5;
    ctx.beginPath();
    ctx.moveTo(PAD_L, PAD_T);
    ctx.lineTo(PAD_L, PAD_T + chartH);
    ctx.lineTo(PAD_L + chartW, PAD_T + chartH);
    ctx.stroke();

    // X-axis label
    ctx.fillStyle = textColor;
    ctx.font = '11px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('Frames', PAD_L + chartW / 2, PAD_T + chartH + 32);

    // Y-axis label
    ctx.save();
    ctx.translate(8, PAD_T + chartH / 2);
    ctx.rotate(-Math.PI / 2);
    ctx.fillText('Time (seconds)', 0, 0);
    ctx.restore();
  }

  /* ── CHART ──────────────────────────────────────── */
  function renderChart(stats) {
    const canvas = document.getElementById('time-chart');
    if (!canvas || !stats) return;
    const ctx = canvas.getContext('2d');

    // Resolve canvas pixel size
    const W = canvas.offsetWidth  || 600;
    const H = canvas.offsetHeight || 220;
    canvas.width  = W * devicePixelRatio;
    canvas.height = H * devicePixelRatio;
    ctx.scale(devicePixelRatio, devicePixelRatio);

    const algos  = ['bubble', 'insertion', 'quick', 'merge'];
    const labels = ['Bubble', 'Insertion', 'Quick', 'Merge'];
    const colors = ['#38bdf8', '#818cf8', '#34d399', '#fb923c'];
    const values = algos.map(a => stats[a] || sortData[a]?.length || 0);
    const maxVal = Math.max(...values) || 1;

    const PAD_L = 50, PAD_R = 20, PAD_T = 20, PAD_B = 40;
    const chartW = W - PAD_L - PAD_R;
    const chartH = H - PAD_T - PAD_B;

    const isLight = document.body.classList.contains('light');
    const gridColor  = isLight ? 'rgba(0,0,0,0.07)'  : 'rgba(255,255,255,0.05)';
    const textColor  = isLight ? 'rgba(0,0,0,0.45)'  : 'rgba(255,255,255,0.35)';
    const axisColor  = isLight ? 'rgba(0,0,0,0.15)'  : 'rgba(255,255,255,0.1)';

    ctx.clearRect(0, 0, W, H);

    // Grid lines
    ctx.strokeStyle = gridColor;
    ctx.lineWidth = 0.5;
    for (let i = 0; i <= 4; i++) {
      const y = PAD_T + chartH - (i / 4) * chartH;
      ctx.beginPath(); ctx.moveTo(PAD_L, y); ctx.lineTo(PAD_L + chartW, y); ctx.stroke();
      ctx.fillStyle = textColor;
      ctx.font = '10px sans-serif';
      ctx.textAlign = 'right';
      ctx.fillText(Math.round(maxVal * i / 4), PAD_L - 6, y + 3);
    }

    // Bars
    const barW = Math.min(60, chartW / algos.length * 0.55);
    const gap  = chartW / algos.length;

    algos.forEach((a, i) => {
      const x    = PAD_L + gap * i + gap / 2 - barW / 2;
      const barH = (values[i] / maxVal) * chartH;
      const y    = PAD_T + chartH - barH;

      // Bar fill
      ctx.fillStyle = colors[i] + '22';
      ctx.strokeStyle = colors[i];
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.roundRect(x, y, barW, barH, [4, 4, 0, 0]);
      ctx.fill();
      ctx.stroke();

      // Value label above bar
      ctx.fillStyle = colors[i];
      ctx.font = '11px sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText(values[i], x + barW / 2, y - 6);

      // X label
      ctx.fillStyle = textColor;
      ctx.font = '11px sans-serif';
      ctx.fillText(labels[i], x + barW / 2, PAD_T + chartH + 18);
    });

    // Axis
    ctx.strokeStyle = axisColor;
    ctx.lineWidth = 0.5;
    ctx.beginPath();
    ctx.moveTo(PAD_L, PAD_T); ctx.lineTo(PAD_L, PAD_T + chartH);
    ctx.lineTo(PAD_L + chartW, PAD_T + chartH); ctx.stroke();
  }

  // Re-render chart on theme change
  document.getElementById('btn-theme')?.addEventListener('click', () => {
    if (sortData?.stats) setTimeout(() => renderChart(sortData.stats), 60);
  });
}