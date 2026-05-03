// app.js — router, state, fetch helpers

export const $  = (sel, root=document) => root.querySelector(sel);
export const $$ = (sel, root=document) => Array.from(root.querySelectorAll(sel));

const COMPACT = new Intl.NumberFormat('en', { notation: 'compact', maximumFractionDigits: 1 });
export const fmt = {
  int:   n => (n ?? 0).toLocaleString(),
  compact: n => COMPACT.format(n ?? 0),
  usd:   n => n == null ? '—' : `$${Number(n).toFixed(2)}`,
  usd4:  n => n == null ? '—' : `$${Number(n).toFixed(4)}`,
  pct:   n => n == null ? '—' : `${(n * 100).toFixed(0)}%`,
  short: (s, n=80) => s == null ? '' : (s.length > n ? `${s.slice(0, n - 1)}…` : s),
  htmlSafe: s => (s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])),
  modelClass: m => {
    const s = (m || '').toLowerCase();
    if (s.includes('opus'))   return 'opus';
    if (s.includes('sonnet')) return 'sonnet';
    if (s.includes('haiku'))  return 'haiku';
    return '';
  },
  modelShort: m => (m || '').replace('claude-', ''),
  ts: t => (t || '').slice(0, 16).replace('T', ' '),
};

export async function api(path, opts) {
  const r = await fetch(path, opts);
  if (!r.ok) throw new Error(`${path} → ${r.status}`);
  return r.json();
}

export const state = { plan: 'api', pricing: null };

const ROUTES = {
  '/overview': () => import('/web/routes/overview.js'),
  '/prompts':  () => import('/web/routes/prompts.js'),
  '/sessions': () => import('/web/routes/sessions.js'),
  '/projects': () => import('/web/routes/projects.js'),
  '/skills':   () => import('/web/routes/skills.js'),
  '/tips':     () => import('/web/routes/tips.js'),
  '/settings': () => import('/web/routes/settings.js'),
  '/about':    () => import('/web/routes/about.js'),
};

function buildTopbar() {
  const wrap = document.createElement('header');
  wrap.className = 'topbar';
  wrap.innerHTML = `
    <div class="brand">Symbolon</div>
    <span class="scope-tag" title="Claude Desktop, claude.ai web, and direct API calls are not tracked here. Cross-check with console.anthropic.com for the full picture.">Claude Code only</span>
    <nav>
      ${Object.keys(ROUTES).map(p => `<a href="#${p}" data-route="${p}">${p.slice(1)}</a>`).join('')}
    </nav>
    <div class="spacer"></div>
    <span class="pill" id="plan-pill">api</span>
    <span class="pill muted" title="Cmd/Ctrl+B blurs sensitive text">⌘B blur</span>
    <button id="quit-btn" class="danger" title="Stop the server">⏻</button>
  `;
  document.body.prepend(wrap);

  let quitArmed = false;
  let quitTimer = null;
  document.getElementById('quit-btn').addEventListener('click', async () => {
    const btn = document.getElementById('quit-btn');
    if (!quitArmed) {
      quitArmed = true;
      btn.textContent = '⏻ confirm?';
      quitTimer = setTimeout(() => {
        quitArmed = false;
        btn.textContent = '⏻';
      }, 3000);
      return;
    }
    clearTimeout(quitTimer);
    btn.disabled = true;
    btn.textContent = '…';
    try {
      const res = await fetch('/api/quit', { method: 'POST' });
      // fetch only rejects on network errors. A 403 from the source-IP guard
      // (non-localhost client) returns OK at the network level — we must
      // check the HTTP status explicitly.
      if (!res.ok) throw new Error(`quit failed: ${res.status}`);
    } catch {
      // Server didn't acknowledge shutdown — restore the button and bail
      // before clearing the page.
      quitArmed = false;
      btn.disabled = false;
      btn.textContent = '⏻';
      return;
    }
    const msg = document.createElement('div');
    msg.style.cssText = 'display:grid;place-items:center;height:100vh;color:#8B98A6;font-family:system-ui;font-size:14px';
    document.body.innerHTML = '';
    document.body.appendChild(msg);
    let t = 3;
    const tick = () => {
      msg.textContent = `Server stopped — closing in ${t}…`;
      if (t-- > 0) setTimeout(tick, 1000);
      else { window.close(); msg.textContent = 'Server stopped — you can close this tab.'; }
    };
    tick();
  });
}

function setActiveTab(routeKey) {
  $$('header.topbar nav a').forEach(a => {
    a.classList.toggle('active', a.dataset.route === routeKey);
  });
}

async function render() {
  const hash = location.hash.replace(/^#/, '') || '/overview';
  const path = hash.split('?')[0];
  let key = path;
  if (path.startsWith('/sessions/')) key = '/sessions';
  setActiveTab(key);
  const loader = ROUTES[key] || ROUTES['/overview'];
  const mod = await loader();
  $('#app').innerHTML = '';
  try {
    await mod.default($('#app'));
  } catch (e) {
    $('#app').innerHTML = `<div class="card"><h2>Error</h2><pre>${fmt.htmlSafe(String(e.stack || e))}</pre></div>`;
  }
}

async function firstRun() {
  if (localStorage.getItem('td.plan-set')) return;
  const plans = Object.entries(state.pricing.plans);
  const overlay = document.createElement('div');
  overlay.className = 'modal-overlay';
  overlay.innerHTML = `
    <div class="modal">
      <h2>Welcome — pick your plan</h2>
      <p>This sets how costs are displayed. Change it later in Settings.</p>
      <select id="firstplan" style="width:100%">
        ${plans.map(([k,v]) => `<option value="${k}">${v.label}${v.monthly ? ` — $${v.monthly}/mo` : ''}</option>`).join('')}
      </select>
      <div class="actions">
        <div class="spacer"></div>
        <button class="primary" id="firstsave">Continue</button>
      </div>
    </div>`;
  document.body.appendChild(overlay);
  await new Promise(res => $('#firstsave', overlay).addEventListener('click', async () => {
    const plan = $('#firstplan', overlay).value;
    await fetch('/api/plan', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ plan }) });
    localStorage.setItem('td.plan-set', '1');
    overlay.remove();
    res();
  }));
  state.plan = (await api('/api/plan')).plan;
}

async function boot() {
  buildTopbar();
  const planResp = await api('/api/plan');
  state.plan = planResp.plan;
  state.pricing = planResp.pricing;
  $('#plan-pill').textContent = state.plan;

  await firstRun();

  window.addEventListener('hashchange', render);
  await render();

  // Privacy blur (Cmd+B / Ctrl+B)
  window.addEventListener('keydown', e => {
    if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'b') {
      e.preventDefault();
      document.body.classList.toggle('privacy-on');
    }
  });

  // Heartbeat — keeps the server alive; absence triggers auto-shutdown after 30s.
  // Also drives offline detection: two consecutive failures flip the UI into
  // an "offline" state with a reconnect prompt.
  let serverOffline = false;
  let hbFailures = 0;
  let banner = null;

  const setOffline = (off) => {
    if (off === serverOffline) return;
    serverOffline = off;
    document.body.classList.toggle('offline', off);
    const pill = $('#plan-pill');
    if (off) {
      pill.textContent = 'offline';
      pill.classList.add('offline-pill');
      showOfflineBanner();
    } else {
      pill.textContent = state.plan;
      pill.classList.remove('offline-pill');
      if (banner) { banner.remove(); banner = null; }
      render();  // refresh stale content
    }
  };

  function showOfflineBanner() {
    if (banner) return;
    banner = document.createElement('div');
    banner.className = 'offline-banner';
    banner.innerHTML = `
      <div>
        <strong>Server is offline.</strong><br>
        Run <code>symbolon start</code> or <code>symbolon dashboard</code>
        in your terminal, then click reconnect.
      </div>
      <button id="reconnect-btn" class="primary">Reconnect</button>
    `;
    document.body.appendChild(banner);
    $('#reconnect-btn').addEventListener('click', async () => {
      const btn = $('#reconnect-btn');
      btn.disabled = true;
      btn.textContent = 'Trying…';
      try {
        const r = await fetch('/api/heartbeat', { method: 'POST' });
        if (r.ok) { hbFailures = 0; setOffline(false); return; }
      } catch { /* fall through */ }
      btn.disabled = false;
      btn.textContent = 'Reconnect';
    });
  }

  // Server build identity captured on first heartbeat. If a later beat
  // reports a different version, the server has been upgraded under us
  // (typically `uv tool install --reinstall`) — hard-reload so we pick
  // up the matching SPA bundle.
  let serverBuild = null;

  const _hb = async () => {
    try {
      const r = await fetch('/api/heartbeat', { method: 'POST' });
      if (r.ok) {
        hbFailures = 0;
        if (serverOffline) setOffline(false);
        try {
          const info = await r.json();
          if (info?.version) {
            const id = `${info.version}@${info.commit || ''}`;
            if (serverBuild === null) serverBuild = id;
            else if (serverBuild !== id) location.reload();
          }
        } catch { /* heartbeat without JSON body is fine */ }
        return;
      }
    } catch { /* fall through */ }
    hbFailures += 1;
    if (hbFailures >= 2) setOffline(true);
  };
  _hb();
  setInterval(_hb, 10000);

  // SSE diff stream
  try {
    const es = new EventSource('/api/stream');
    es.onmessage = ev => {
      try {
        const evt = JSON.parse(ev.data);
        if (evt.type === 'scan') render();
      } catch {}
    };
  } catch {}
}

boot();
