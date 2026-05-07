import { api, fmt } from '/web/app.js';

export default async function (root) {
  const info = await api('/api/about');
  const commit = info.commit || 'unknown';
  const builtAt = info.built_at ? fmt.ts(info.built_at) : 'source checkout';
  const repo = 'https://github.com/ChristianLemer/symbolon';
  const commitLink = info.commit
    ? `<a href="${repo}/commit/${fmt.htmlSafe(info.commit)}" target="_blank" rel="noopener">${fmt.htmlSafe(commit)}</a>`
    : fmt.htmlSafe(commit);

  root.innerHTML = `
    <div class="card">
      <h2>About</h2>
      <table>
        <tbody>
          <tr><td class="muted">Version</td><td><code>${fmt.htmlSafe(info.version)}</code></td></tr>
          <tr><td class="muted">Commit</td><td><code>${commitLink}</code></td></tr>
          <tr><td class="muted">Built</td><td>${fmt.htmlSafe(builtAt)}</td></tr>
        </tbody>
      </table>
      <p class="muted" style="margin-top:16px;font-size:12px">
        Source: <a href="${repo}" target="_blank" rel="noopener">github.com/ChristianLemer/symbolon</a>
      </p>
    </div>`;
}
