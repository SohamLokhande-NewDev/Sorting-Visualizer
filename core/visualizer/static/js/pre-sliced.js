/* ============================================================
   PRESLICED.JS — Client-side sorting visualizer
   Handles: image loading, slicing detection, frame generation,
            animation engine, and all 4 algorithm hooks.
   ============================================================ */

(function () {
  'use strict';

  /* ── DOM REFS ─────────────────────────────────────────── */
  const psFileInput  = document.getElementById('ps-img-file');
  const psDropZone   = document.getElementById('ps-drop-zone');
  const psFileLabel  = document.getElementById('ps-file-label');
  const psToggle     = document.getElementById('ps-toggle');
  const psStartBtn   = document.getElementById('ps-start-btn');
  const psVizArea    = document.getElementById('ps-viz-area');
  const psSliceStage = document.getElementById('ps-slice-stage');
  const psPlayBtn    = document.getElementById('ps-play-btn');
  const psResetBtn   = document.getElementById('ps-reset-btn');
  const psProgress   = document.getElementById('ps-progress-fill');
  const psStepCount  = document.getElementById('ps-step-counter');
  const psAlgoBadge  = document.getElementById('ps-algo-badge');
  const psSpeedCtrl  = document.getElementById('ps-speed');

  if (!psFileInput) return; // guard — only runs on index.html

  /* ── STATE ────────────────────────────────────────────── */
  let loadedImage   = null;   // HTMLImageElement
  let sliceDataURLs = [];     // array of base64 slice images
  let frames        = [];     // array of frame snapshots [{order, highlight, swap, active, mergeGroups}]
  let frameIndex    = 0;
  let playing       = false;
  let animTimer     = null;
  let selectedAlgo  = 'merge';

  /* ── FILE INPUT + DRAG & DROP ─────────────────────────── */
  psFileInput.addEventListener('change', function () {
    if (this.files[0]) handleFile(this.files[0]);
  });

  ['dragenter', 'dragover'].forEach(ev =>
    psDropZone.addEventListener(ev, e => { e.preventDefault(); psDropZone.classList.add('drag-over'); })
  );
  ['dragleave', 'drop'].forEach(ev =>
    psDropZone.addEventListener(ev, e => { e.preventDefault(); psDropZone.classList.remove('drag-over'); })
  );
  psDropZone.addEventListener('drop', e => {
    const file = e.dataTransfer.files[0];
    if (file && file.type.startsWith('image/')) handleFile(file);
  });

  function handleFile(file) {
    psFileLabel.innerHTML = '<span>' + file.name + '</span>';
    const reader = new FileReader();
    reader.onload = ev => {
      const img = new Image();
      img.onload = () => {
        loadedImage = img;
        psStartBtn.disabled = false;
        psStartBtn.textContent = 'Start Visualization →';
      };
      img.src = ev.target.result;
    };
    reader.readAsDataURL(file);
  }

  /* ── ALGO RADIO SYNC ──────────────────────────────────── */
  document.querySelectorAll('input[name="ps_algo"]').forEach(radio => {
    radio.addEventListener('change', () => {
      selectedAlgo = radio.value;
      updateAlgoBadge();
    });
  });

  function updateAlgoBadge() {
    const names = {
      merge:     'Merge Sort',
      bubble:    'Bubble Sort',
      selection: 'Selection Sort',
      insertion: 'Insertion Sort',
    };
    if (psAlgoBadge) {
      psAlgoBadge.textContent = names[selectedAlgo] || selectedAlgo;
      psAlgoBadge.className   = 'algo-badge';
    }
  }

  /* ── START BUTTON ─────────────────────────────────────── */
  psStartBtn.addEventListener('click', () => {
    if (!loadedImage) return;

    stopAnimation();
    frameIndex = 0;

    const isPreSliced = psToggle && psToggle.checked;
    sliceDataURLs = isPreSliced
      ? detectAndExtractSlices(loadedImage)   // equal-width detection
      : sliceImageEvenly(loadedImage, 8);      // default 8 slices

    if (sliceDataURLs.length < 2) {
      alert('Could not extract enough slices. Please try a different image.');
      return;
    }

    // Generate frames via selected algorithm
    const indices = sliceDataURLs.map((_, i) => i);
    const shuffled = shuffleArray([...indices]);
    frames = generateFrames(selectedAlgo, shuffled, sliceDataURLs.length);

    // Show viz area
    psVizArea.classList.add('active');
    psVizArea.scrollIntoView({ behavior: 'smooth', block: 'nearest' });

    // Render first frame
    renderFrame(frames[0]);
    updateUI();
    updateAlgoBadge();
    psAlgoBadge.classList.add('running');
  });

  /* ── PLAY / PAUSE ─────────────────────────────────────── */
  psPlayBtn.addEventListener('click', () => {
    if (playing) stopAnimation();
    else         startAnimation();
  });

  /* ── RESET ────────────────────────────────────────────── */
  psResetBtn.addEventListener('click', () => {
    stopAnimation();
    frameIndex = 0;
    if (frames.length > 0) renderFrame(frames[0]);
    updateUI();
    if (psAlgoBadge) {
      psAlgoBadge.className = 'algo-badge running';
    }
  });

  function startAnimation() {
    if (frameIndex >= frames.length - 1) { frameIndex = 0; }
    playing = true;
    psPlayBtn.textContent = '⏸ Pause';
    psPlayBtn.classList.add('playing');
    if (psAlgoBadge) psAlgoBadge.className = 'algo-badge running';

    function tick() {
      if (frameIndex >= frames.length - 1) {
        stopAnimation();
        if (psAlgoBadge) psAlgoBadge.className = 'algo-badge done';
        psAlgoBadge.textContent += ' ✓';
        return;
      }
      frameIndex++;
      renderFrame(frames[frameIndex]);
      updateUI();
      animTimer = setTimeout(tick, getDelay());
    }
    tick();
  }

  function stopAnimation() {
    playing = false;
    clearTimeout(animTimer);
    psPlayBtn.textContent = '▶ Play';
    psPlayBtn.classList.remove('playing');
  }

  function getDelay() {
    const speed = parseInt(psSpeedCtrl ? psSpeedCtrl.value : 300);
    return Math.max(50, 880 - speed);
  }

  /* ── RENDER FRAME ─────────────────────────────────────── */
  function renderFrame(frame) {
    if (!frame || !psSliceStage) return;
    psSliceStage.innerHTML = '';

    const { order, highlight = [], swap = [], active = [], mergeGroups = [] } = frame;
    const stageH = psSliceStage.clientHeight || 180;
    const sliceW = Math.max(18, Math.floor((psSliceStage.clientWidth - order.length * 3) / order.length));

    order.forEach(idx => {
      const block = document.createElement('div');
      block.className = 'slice-block';
      block.style.width  = sliceW + 'px';
      block.style.height = stageH + 'px';
      block.dataset.idx  = idx;

      if (sliceDataURLs[idx]) {
        const img = document.createElement('img');
        img.src = sliceDataURLs[idx];
        img.alt = 'slice-' + idx;
        block.appendChild(img);
      } else {
        // Fallback: coloured placeholder
        block.style.background = hslFromIndex(idx, sliceDataURLs.length);
        block.style.opacity = '0.7';
      }

      if (highlight.includes(idx)) block.classList.add('highlight');
      if (swap.includes(idx))      block.classList.add('swap');
      if (active.includes(idx))    block.classList.add('active');
      if (mergeGroups.some(g => g.includes(idx))) block.classList.add('merge-group');

      psSliceStage.appendChild(block);
    });
  }

  function hslFromIndex(idx, total) {
    const hue = Math.round((idx / Math.max(total, 1)) * 280);
    return `hsl(${hue}, 60%, 35%)`;
  }

  function updateUI() {
    const pct = frames.length > 1
      ? ((frameIndex / (frames.length - 1)) * 100).toFixed(1)
      : 100;
    if (psProgress)  psProgress.style.width   = pct + '%';
    if (psStepCount) psStepCount.textContent   = 'Step ' + frameIndex + ' / ' + (frames.length - 1);
  }

  /* ══════════════════════════════════════════════════════
     IMAGE SLICING
  ══════════════════════════════════════════════════════ */

  /**
   * sliceImageEvenly — cuts image into n equal vertical strips.
   * Returns array of base64 data-URLs.
   */
  function sliceImageEvenly(img, n) {
    const w = Math.floor(img.naturalWidth / n);
    const h = img.naturalHeight;
    const result = [];
    for (let i = 0; i < n; i++) {
      const canvas = document.createElement('canvas');
      canvas.width  = w;
      canvas.height = h;
      canvas.getContext('2d').drawImage(img, i * w, 0, w, h, 0, 0, w, h);
      result.push(canvas.toDataURL());
    }
    return result;
  }

  /**
   * detectAndExtractSlices — analyses column-wise variance to find natural
   * vertical boundaries in a pre-sliced image, then extracts each slice.
   * Falls back to even slicing if detection is inconclusive.
   *
   * HOOK: Replace this function body with a more sophisticated
   * boundary-detection algorithm if needed (e.g. edge detection via pixel diff).
   */
  function detectAndExtractSlices(img) {
    const canvas = document.createElement('canvas');
    canvas.width  = img.naturalWidth;
    canvas.height = img.naturalHeight;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(img, 0, 0);

    const W = canvas.width;
    const H = canvas.height;
    const data = ctx.getImageData(0, 0, W, H).data;

    // Column-wise vertical-gradient variance
    const colVariance = new Float32Array(W);
    for (let x = 0; x < W; x++) {
      let sumSq = 0, sum = 0, cnt = 0;
      for (let y = 1; y < H; y++) {
        const off  = (y * W + x) * 4;
        const offP = ((y - 1) * W + x) * 4;
        const diff = Math.abs(data[off] - data[offP]) +
                     Math.abs(data[off+1] - data[offP+1]) +
                     Math.abs(data[off+2] - data[offP+2]);
        sumSq += diff * diff;
        sum   += diff;
        cnt++;
      }
      colVariance[x] = cnt ? (sumSq / cnt - (sum / cnt) ** 2) : 0;
    }

    // Find low-variance columns as potential boundaries
    const mean = colVariance.reduce((a, b) => a + b, 0) / W;
    const threshold = mean * 0.3;

    const boundaries = [0];
    let inLow = false;
    for (let x = 1; x < W - 1; x++) {
      if (colVariance[x] < threshold && !inLow) {
        boundaries.push(x);
        inLow = true;
      } else if (colVariance[x] >= threshold) {
        inLow = false;
      }
    }
    boundaries.push(W);

    // Need at least 2 slices
    if (boundaries.length < 3) {
      return sliceImageEvenly(img, 8);
    }

    // Cap at 32 slices
    const sliceCount = Math.min(boundaries.length - 1, 32);
    const result = [];
    for (let i = 0; i < sliceCount; i++) {
      const x1 = boundaries[i];
      const x2 = boundaries[i + 1];
      const sw  = x2 - x1;
      const sc  = document.createElement('canvas');
      sc.width  = sw;
      sc.height = H;
      sc.getContext('2d').drawImage(img, x1, 0, sw, H, 0, 0, sw, H);
      result.push(sc.toDataURL());
    }
    return result;
  }

  /* ══════════════════════════════════════════════════════
     FRAME GENERATOR  (sorting algorithm hooks)
     Each function receives a shuffled array of indices and
     returns an array of frame objects:
       { order: number[], highlight: number[], swap: number[],
         active: number[], mergeGroups: number[][] }
  ══════════════════════════════════════════════════════ */

  function generateFrames(algo, arr, n) {
    const fns = {
      bubble:    generateBubbleFrames,
      selection: generateSelectionFrames,
      insertion: generateInsertionFrames,
      merge:     generateMergeFrames,
    };
    const fn = fns[algo] || generateBubbleFrames;
    return fn([...arr], n);
  }

  /** Snapshot helper */
  function snap(arr, highlight = [], swap = [], active = [], mergeGroups = []) {
    return {
      order: [...arr],
      highlight: [...highlight],
      swap:      [...swap],
      active:    [...active],
      mergeGroups: mergeGroups.map(g => [...g]),
    };
  }

  /* ── BUBBLE SORT ──────────────────────────────────────
     Adjacent comparisons; swap animation on each exchange.
     Time: O(n²)  Space: O(1)
  ─────────────────────────────────────────────────────── */
  function generateBubbleFrames(arr) {
    const result = [snap(arr)];
    const n = arr.length;
    for (let i = 0; i < n - 1; i++) {
      for (let j = 0; j < n - i - 1; j++) {
        // Highlight: comparing j and j+1
        result.push(snap(arr, [arr[j], arr[j + 1]]));
        if (arr[j] > arr[j + 1]) {
          // Swap frame
          result.push(snap(arr, [], [arr[j], arr[j + 1]]));
          [arr[j], arr[j + 1]] = [arr[j + 1], arr[j]];
          result.push(snap(arr));
        }
      }
      // Mark sorted element at end
      result.push(snap(arr, [], [], [], []));
    }
    result.push(snap(arr)); // final sorted state
    return result;
  }

  /* ── SELECTION SORT ───────────────────────────────────
     Find minimum; highlight it; swap to position.
     Time: O(n²)  Space: O(1)
  ─────────────────────────────────────────────────────── */
  function generateSelectionFrames(arr) {
    const result = [snap(arr)];
    const n = arr.length;
    for (let i = 0; i < n - 1; i++) {
      let minIdx = i;
      result.push(snap(arr, [], [], [arr[minIdx]]));   // active = current min
      for (let j = i + 1; j < n; j++) {
        result.push(snap(arr, [arr[j]], [], [arr[minIdx]])); // comparing j to min
        if (arr[j] < arr[minIdx]) {
          minIdx = j;
          result.push(snap(arr, [], [], [arr[minIdx]])); // new min found
        }
      }
      if (minIdx !== i) {
        result.push(snap(arr, [], [arr[i], arr[minIdx]])); // swap
        [arr[i], arr[minIdx]] = [arr[minIdx], arr[i]];
        result.push(snap(arr));
      }
    }
    result.push(snap(arr));
    return result;
  }

  /* ── INSERTION SORT ───────────────────────────────────
     Shift elements right; insert key at correct position.
     Time: O(n²)  Space: O(1)
  ─────────────────────────────────────────────────────── */
  function generateInsertionFrames(arr) {
    const result = [snap(arr)];
    const n = arr.length;
    for (let i = 1; i < n; i++) {
      const key = arr[i];
      result.push(snap(arr, [], [], [key]));   // active = element being inserted
      let j = i - 1;
      while (j >= 0 && arr[j] > key) {
        result.push(snap(arr, [arr[j], key]));  // comparing
        arr[j + 1] = arr[j];
        result.push(snap(arr, [], [arr[j + 1], key])); // shift
        j--;
      }
      arr[j + 1] = key;
      result.push(snap(arr));
    }
    result.push(snap(arr));
    return result;
  }

  /* ── MERGE SORT ───────────────────────────────────────
     Recursive splitting → merging step-by-step.
     Shows merge groups as visual bracket groups.
     Time: O(n log n)  Space: O(n)

     HOOK: This is a frame-capture wrapper around a real
     merge sort. Replace _mergeSort with a backend call
     or a more detailed frame emitter as needed.
  ─────────────────────────────────────────────────────── */
  function generateMergeFrames(arr) {
    const result = [snap(arr)];

    function _merge(a, left, mid, right) {
      const L = a.slice(left, mid + 1);
      const R = a.slice(mid + 1, right + 1);

      // Show the two groups being merged
      const lGroup = a.slice(left, mid + 1);
      const rGroup = a.slice(mid + 1, right + 1);
      result.push(snap(a, [], [], [], [lGroup, rGroup]));

      let i = 0, j = 0, k = left;
      while (i < L.length && j < R.length) {
        result.push(snap(a, [L[i], R[j]], [], [], [lGroup, rGroup]));
        if (L[i] <= R[j]) {
          a[k++] = L[i++];
        } else {
          a[k++] = R[j++];
        }
        result.push(snap(a, [], [], [], []));
      }
      while (i < L.length) { a[k++] = L[i++]; result.push(snap(a)); }
      while (j < R.length) { a[k++] = R[j++]; result.push(snap(a)); }
    }

    function _mergeSort(a, left, right) {
      if (left >= right) return;
      const mid = Math.floor((left + right) / 2);
      _mergeSort(a, left, mid);
      _mergeSort(a, mid + 1, right);
      _merge(a, left, mid, right);
    }

    _mergeSort(arr, 0, arr.length - 1);
    result.push(snap(arr));
    return result;
  }

  /* ══════════════════════════════════════════════════════
     UTILITIES
  ══════════════════════════════════════════════════════ */

  /** Fisher-Yates shuffle */
  function shuffleArray(arr) {
    for (let i = arr.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [arr[i], arr[j]] = [arr[j], arr[i]];
    }
    return arr;
  }

})();