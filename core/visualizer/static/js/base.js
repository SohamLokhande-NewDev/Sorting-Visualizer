/* ============================================================
   BASE.JS — Sorting Visualiser · Shared Scripts
   ============================================================ */

(function () {
  'use strict';

  /* ── CURSOR ─────────────────────────────────────────── */
  const dot    = document.getElementById('cursor-dot');
  const ring   = document.getElementById('cursor-ring');
  const trail  = document.getElementById('cursor-trail');
  const ctx    = trail ? trail.getContext('2d') : null;

  function resizeTrail() {
    if (!trail) return;
    trail.width  = window.innerWidth;
    trail.height = window.innerHeight;
  }
  resizeTrail();
  window.addEventListener('resize', resizeTrail);

  let mouse   = { x: window.innerWidth / 2,  y: window.innerHeight / 2  };
  let ringPos = { x: mouse.x, y: mouse.y };
  let particles = [];

  document.addEventListener('mousemove', e => {
    mouse.x = e.clientX;
    mouse.y = e.clientY;
    if (!ctx) return;
    particles.push({
      x: e.clientX, y: e.clientY,
      alpha: 0.5,
      radius: 2.5 + Math.random() * 2,
      vx: (Math.random() - 0.5) * 0.5,
      vy: (Math.random() - 0.5) * 0.5,
    });
  });

  function lerp(a, b, t) { return a + (b - a) * t; }

  function getCursorColor() {
    return document.body.classList.contains('light')
      ? 'rgba(3,105,161,' : 'rgba(56,189,248,';
  }

  function animateCursor() {
    if (ctx) {
      ctx.clearRect(0, 0, trail.width, trail.height);
      for (let i = particles.length - 1; i >= 0; i--) {
        const p = particles[i];
        p.alpha  -= 0.025;
        p.radius *= 0.96;
        p.x += p.vx;
        p.y += p.vy;
        if (p.alpha <= 0) { particles.splice(i, 1); continue; }
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
        ctx.fillStyle = getCursorColor() + p.alpha + ')';
        ctx.fill();
      }
    }
    ringPos.x = lerp(ringPos.x, mouse.x, 0.12);
    ringPos.y = lerp(ringPos.y, mouse.y, 0.12);
    if (dot)  { dot.style.left  = mouse.x + 'px'; dot.style.top  = mouse.y + 'px'; }
    if (ring) { ring.style.left = ringPos.x + 'px'; ring.style.top = ringPos.y + 'px'; }
    requestAnimationFrame(animateCursor);
  }
  animateCursor();

  /* ── THEME TOGGLE ────────────────────────────────────── */
  const btnTheme = document.getElementById('btn-theme');
  const savedTheme = localStorage.getItem('sv-theme');
  if (savedTheme === 'light') document.body.classList.add('light');
  updateThemeIcon();

  function updateThemeIcon() {
    if (!btnTheme) return;
    btnTheme.textContent = document.body.classList.contains('light') ? '☀' : '◑';
    btnTheme.title = document.body.classList.contains('light') ? 'Switch to dark' : 'Switch to light';
  }

  if (btnTheme) {
    btnTheme.addEventListener('click', () => {
      document.body.classList.toggle('light');
      localStorage.setItem('sv-theme', document.body.classList.contains('light') ? 'light' : 'dark');
      updateThemeIcon();
    });
  }

  /* ── PROFILE DROPDOWN ────────────────────────────────── */
  const btnProfile  = document.getElementById('btn-profile');
  const profileDrop = document.getElementById('profile-dropdown');

  if (btnProfile && profileDrop) {
    btnProfile.addEventListener('click', e => {
      e.stopPropagation();
      profileDrop.classList.toggle('open');
    });
    document.addEventListener('click', () => profileDrop.classList.remove('open'));
    profileDrop.addEventListener('click', e => e.stopPropagation());
  }

  /* ── LOGIN STATE ─────────────────────────────────────── */
  const btnLogin = document.getElementById('btn-login');
  const storedUser = localStorage.getItem('sv-user');
  if (btnLogin && storedUser) {
    btnLogin.textContent = storedUser;
    btnLogin.classList.add('active');
    btnLogin.href = '/logout/';
  }

  /* ── SCROLL REVEAL ───────────────────────────────────── */
  const revealEls = document.querySelectorAll('.reveal');
  const revealObs = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        revealObs.unobserve(entry.target);
      }
    });
  }, { threshold: 0.12 });
  revealEls.forEach(el => revealObs.observe(el));

})();