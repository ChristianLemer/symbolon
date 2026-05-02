import { api, fmt, state } from '/web/app.js';
import { barChart, donutChart, groupedBarChart, stackedBarChart } from '/web/charts.js';

const RANGES = [
  { key: 'today', dayOffset: 0 },
  { key: 'd1', dayOffset: 1 },
  { key: 'd2', dayOffset: 2 },
  { key: 'd3', dayOffset: 3 },
  { key: 'd4', dayOffset: 4 },
  { key: 'd5', dayOffset: 5 },
  { key: 'd6', dayOffset: 6 },
  { key: '7d',  label: '7d',  days: 7 },
  { key: '30d', label: '30d', days: 30 },
  { key: '90d', label: '90d', days: 90 },
  { key: 'all', label: 'All', days: null },
];

const isDayRange = (r) => r.dayOffset !== undefined;

function readRange() {
  const q = (location.hash.split('?')[1] || '');
  const m = /(?:^|&)range=([^&]+)/.exec(q);
  const k = m && decodeURIComponent(m[1]);
  return RANGES.find(r => r.key === k) || RANGES[0];
}

function writeRange(key) {
  const base = (location.hash.replace(/^#/, '').split('?')[0]) || '/overview';
  location.hash = `#${base}?range=${encodeURIComponent(key)}`;
}

// Server is the canonical source for cutoff-aware day windows — see
// symbolon/util.py::today_range_local. Defaults to a 4 a.m. local
// cutoff so late-night sessions count toward yesterday.
async function dayWindow(offset) {
  return await api(`/api/today/range?offset=${offset}`);
}

function nDaysAgoIso(days) {
  return new Date(Date.now() - days * 86400 * 1000).toISOString();
}

function withSince(url, since, until) {
  if (!since) return url;
  const sep = url.includes('?') ? '&' : '?';
  let result = `${url}${sep}since=${encodeURIComponent(since)}`;
  if (until) result += `&until=${encodeURIComponent(until)}`;
  return result;
}

// Short weekday name for a YYYY-MM-DD day string. Noon UTC avoids DST edges.
function weekdayShort(dayStr) {
  return new Date(`${dayStr}T12:00:00Z`).toLocaleDateString(undefined, { weekday: 'short' });
}

// Compute the day string (YYYY-MM-DD) for `today.day` minus `offset` days.
function dayStringFor(todayDayStr, offset) {
  const [y, m, d] = todayDayStr.split('-').map(Number);
  const dt = new Date(Date.UTC(y, m - 1, d));
  dt.setUTCDate(dt.getUTCDate() - offset);
  return dt.toISOString().slice(0, 10);
}

export default async function (root) {
  const range = readRange();
  // Always fetch today's window — used to label weekday tabs and as the
  // selected window when the active range is a day range.
  const todayMeta = await api('/api/today/range');
  const win = isDayRange(range) ? (range.dayOffset === 0 ? todayMeta : await dayWindow(range.dayOffset)) : null;

  const since = win ? win.since : (range.days ? nDaysAgoIso(range.days) : null);
  const until = win ? win.until : null;

  const [totals, projects, sessions, tools, daily, byModel] = await Promise.all([
    api(withSince('/api/overview', since, until)),
    api(withSince('/api/projects', since, until)),
    api(withSince('/api/sessions?limit=10', since, until)),
    api(withSince('/api/tools', since, until)),
    api(withSince('/api/daily', since, until)),
    api(withSince('/api/by-model', since, until)),
  ]);

  const cacheCreate =
    (totals.cache_create_5m_tokens || 0) +
    (totals.cache_create_1h_tokens || 0);

  function monthlyRate(cost) {
    if (isDayRange(range)) {
      // A complete past day projects directly: today's cost × 30.
      if (range.dayOffset > 0) return (cost || 0) * 30;
      // Today is in progress — extrapolate hourly pace to a full month.
      const fracOfDay = (Date.now() - Date.parse(win.since)) / 86400000;
      if (fracOfDay < 0.05) return null;  // first ~72 min of the cutoff window
      return (cost || 0) / fracOfDay * 30;
    }
    if (!range.days) return null;
    return (cost || 0) / range.days * 30;
  }
  const monthly = monthlyRate(totals.cost_usd);

  const kpi = (label, compactVal, fullVal, cls = '') => `
    <div class="card kpi ${cls}">
      <div class="label">${label}</div>
      <div class="value" title="${fullVal}">${compactVal}</div>
    </div>`;

  const tabLabel = (r) => {
    if (r.label) return r.label;
    if (isDayRange(r)) {
      const wd = weekdayShort(dayStringFor(todayMeta.day, r.dayOffset));
      return r.dayOffset === 0 ? `Today (${wd})` : wd;
    }
    return r.key;
  };
  const rangeTabs = `
    <div class="range-tabs" role="tablist">
      ${RANGES.map(r => `<button data-range="${r.key}" class="${r.key === range.key ? 'active' : ''}">${tabLabel(r)}</button>`).join('')}
    </div>`;

  root.innerHTML = `
    <div class="flex" style="margin-bottom:14px">
      <h2 style="margin:0;font-size:16px;letter-spacing:-0.01em">Overview</h2>
      <span class="muted" style="font-size:12px">${isDayRange(range) ? (range.dayOffset === 0 ? `since ${String(win.day_starts_at_hour).padStart(2, '0')}:00` : `${win.day} · ${String(win.day_starts_at_hour).padStart(2, '0')}:00–${String(win.day_starts_at_hour).padStart(2, '0')}:00 next`) : range.days ? `last ${range.days} days` : 'all time'}</span>
      <div class="spacer"></div>
      ${rangeTabs}
    </div>

    <div class="row cols-8">
      ${kpi('Sessions',     fmt.int(totals.sessions),       fmt.int(totals.sessions))}
      ${kpi('Turns',        fmt.int(totals.turns),          fmt.int(totals.turns))}
      ${kpi('Input',        fmt.compact(totals.input_tokens),       `${fmt.int(totals.input_tokens)} tokens`)}
      ${kpi('Output',       fmt.compact(totals.output_tokens),      `${fmt.int(totals.output_tokens)} tokens`)}
      ${kpi('Cache read',   fmt.compact(totals.cache_read_tokens),  `${fmt.int(totals.cache_read_tokens)} tokens`)}
      ${kpi('Cache create', fmt.compact(cacheCreate),               `${fmt.int(cacheCreate)} tokens`)}
      <div class="card kpi cost">
        <div class="label">Est. cost</div>
        <div class="value" title="${fmt.usd(totals.cost_usd)}">${fmt.usd(totals.cost_usd)}</div>
        ${planSubtitle()}
      </div>
      <div class="card kpi">
        <div class="label">Est. $/mo</div>
        <div class="value" title="${monthly !== null ? `${fmt.usd(monthly)}/mo` : 'n/a'}">${monthly !== null ? fmt.usd(monthly) : '—'}</div>
        <div class="sub">${isDayRange(range) ? (range.dayOffset === 0 ? "today's pace × 30" : "this day × 30") : range.days ? `×${(30/range.days).toFixed(1)} (${range.days}d rate)` : 'all time'}</div>
      </div>
    </div>

    <details class="card glossary" style="margin-top:16px">
      <summary><h3 style="display:inline-block;margin:0">What do these numbers mean?</h3><span class="muted" style="font-size:12px">— click to expand</span></summary>
      <dl>
        <dt>Session</dt><dd>One run of Claude Code (from <code>claude</code> to exit). Each session is a single <code>.jsonl</code> file.</dd>
        <dt>Turn</dt><dd>One message you sent to Claude. Each turn triggers a response (possibly with tool calls in between).</dd>
        <dt>Input tokens</dt><dd>The new text you (and tool results) sent to Claude this turn. Billed at the full input rate.</dd>
        <dt>Output tokens</dt><dd>The text Claude wrote back. Billed at the highest rate — usually the biggest cost driver per turn.</dd>
        <dt>Cache read</dt><dd>Tokens Claude re-used from a cache (your CLAUDE.md, previously-read files, the conversation so far). ~10× cheaper than fresh input. High cache-read counts = good cost hygiene.</dd>
        <dt>Cache create</dt><dd>Writing something into the cache for the first time. One-time cost; pays off on the next turn.</dd>
        <dt>Billable tokens</dt><dd>Input + Output + Cache create. Cache reads are billed separately (and much cheaper).</dd>
      </dl>
    </details>

    <div class="row cols-2" style="margin-top:16px">
      <div class="card">
        <h3>Your daily work</h3>
        <p class="muted" style="margin:-4px 0 10px;font-size:12px">Tokens you paid for: what you sent (<b>input</b>), what Claude wrote (<b>output</b>), and what got stored for re-use (<b>cache create</b>).</p>
        <div id="ch-daily-billable" style="height:260px"></div>
      </div>
      <div class="card">
        <h3>Daily cache reads</h3>
        <p class="muted" style="margin:-4px 0 10px;font-size:12px"><b>Cache reads</b> are cheap re-uses of things Claude already saw (like your CLAUDE.md). They cost ~10× less than regular input tokens — high numbers here are a good thing.</p>
        <div id="ch-daily-cache" style="height:260px"></div>
      </div>
    </div>

    <div class="row cols-2" style="margin-top:16px">
      <div class="card"><h3>Tokens by project</h3><div id="ch-projects" style="height:320px"></div></div>
      <div class="card">
        <h3>Token usage by model</h3>
        <p class="muted" style="margin:-4px 0 4px;font-size:12px">Share of billable tokens per Claude model.</p>
        <div id="ch-model" style="height:300px"></div>
      </div>
    </div>

    <div class="row cols-2" style="margin-top:16px">
      <div class="card"><h3>Top tools (by call count)</h3><div id="ch-tools" style="height:320px"></div></div>
      <div class="card">
        <h3 style="display:flex;align-items:center"><span>Recent sessions</span><span class="spacer"></span><a href="#/sessions" style="font-weight:400;font-size:12px">all →</a></h3>
        <table>
          <thead><tr><th>started</th><th>project</th><th class="num">tokens</th></tr></thead>
          <tbody>
            ${sessions.map(s => `
              <tr>
                <td class="mono">${fmt.ts(s.started)}</td>
                <td><a href="#/sessions/${encodeURIComponent(s.session_id)}">${fmt.htmlSafe(s.project_name || s.project_slug)}</a></td>
                <td class="num">${fmt.compact(s.tokens)}</td>
              </tr>`).join('') || '<tr><td colspan="3" class="muted">no sessions in this range</td></tr>'}
          </tbody>
        </table>
      </div>
    </div>
  `;

  // range buttons
  root.querySelectorAll('.range-tabs button').forEach(btn => {
    btn.addEventListener('click', () => writeRange(btn.dataset.range));
  });

  // Your daily work — billable tokens (input + output + cache create)
  stackedBarChart(document.getElementById('ch-daily-billable'), {
    categories: daily.map(d => d.day),
    series: [
      { name: 'input',        values: daily.map(d => d.input_tokens),        color: '#4A9EFF' },
      { name: 'output',       values: daily.map(d => d.output_tokens),       color: '#7C5CFF' },
      { name: 'cache create', values: daily.map(d => d.cache_create_tokens), color: '#E8A23B' },
    ],
  });

  // Daily cache reads (separate — scale is 100× larger)
  stackedBarChart(document.getElementById('ch-daily-cache'), {
    categories: daily.map(d => d.day),
    series: [
      { name: 'cache read', values: daily.map(d => d.cache_read_tokens), color: '#3FB68B' },
    ],
  });

  // by-model doughnut
  donutChart(document.getElementById('ch-model'),
    byModel.map(m => ({
      name: fmt.modelShort(m.model) || 'unknown',
      value: (m.input_tokens || 0) + (m.output_tokens || 0)
           + (m.cache_create_5m_tokens || 0) + (m.cache_create_1h_tokens || 0),
    })).filter(d => d.value > 0),
  );

  // tokens by project — input vs output
  const topProjects = projects.slice(0, 8);
  groupedBarChart(document.getElementById('ch-projects'), {
    categories: topProjects.map(p => {
      const name = p.project_name || p.project_slug;
      return name.length > 20 ? `${name.slice(0, 19)}…` : name;
    }),
    series: [
      { name: 'input',  values: topProjects.map(p => p.input_tokens  || 0), color: '#4A9EFF' },
      { name: 'output', values: topProjects.map(p => p.output_tokens || 0), color: '#7C5CFF' },
    ],
  });

  // top tools
  const topTools = tools.slice(0, 8);
  barChart(document.getElementById('ch-tools'), {
    categories: topTools.map(t => t.tool_name),
    values: topTools.map(t => t.calls),
    color: '#7C5CFF',
  });
}

function planSubtitle() {
  if (!state.pricing || state.plan === 'api') return '';
  const p = state.pricing.plans?.[state.plan];
  if (!p?.monthly) return '';
  return `<div class="sub">pay $${p.monthly}/mo on ${fmt.htmlSafe(p.label)}</div>`;
}
