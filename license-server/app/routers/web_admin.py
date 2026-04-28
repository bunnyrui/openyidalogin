from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["web-admin"])


ADMIN_HTML = r'''
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>授权管理后台</title>
  <style>
    :root { --bg:#f6f7fb; --card:#fff; --text:#1f2937; --muted:#6b7280; --primary:#2563eb; --danger:#dc2626; --ok:#16a34a; --border:#e5e7eb; }
    * { box-sizing: border-box; }
    body { margin:0; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"PingFang SC","Microsoft YaHei",Arial,sans-serif; background:var(--bg); color:var(--text); }
    header { height:58px; display:flex; align-items:center; justify-content:space-between; padding:0 24px; background:#111827; color:#fff; }
    header h1 { margin:0; font-size:18px; }
    header .right { display:flex; gap:12px; align-items:center; }
    main { max-width:1280px; margin:24px auto; padding:0 20px 40px; }
    .card { background:var(--card); border:1px solid var(--border); border-radius:14px; box-shadow:0 4px 18px rgba(17,24,39,.05); padding:18px; margin-bottom:18px; }
    .login { max-width:420px; margin:80px auto; }
    label { display:block; font-size:13px; color:var(--muted); margin-bottom:6px; }
    input, select, textarea { width:100%; border:1px solid var(--border); border-radius:10px; padding:10px 12px; font-size:14px; outline:none; background:#fff; }
    input:focus, textarea:focus { border-color:var(--primary); }
    textarea { resize:vertical; min-height:42px; }
    button { border:0; border-radius:10px; padding:9px 13px; font-size:14px; cursor:pointer; background:var(--primary); color:#fff; }
    button.secondary { background:#374151; }
    button.ghost { background:#eef2ff; color:#1d4ed8; }
    button.danger { background:var(--danger); }
    button.ok { background:var(--ok); }
    button:disabled { opacity:.55; cursor:not-allowed; }
    .grid { display:grid; grid-template-columns: repeat(6, 1fr); gap:12px; align-items:end; }
    .grid .span2 { grid-column: span 2; }
    .grid .span3 { grid-column: span 3; }
    .tabs { display:flex; gap:8px; margin-bottom:14px; }
    .tabs button { background:#fff; color:#111827; border:1px solid var(--border); }
    .tabs button.active { background:var(--primary); color:#fff; border-color:var(--primary); }
    table { width:100%; border-collapse:collapse; font-size:13px; }
    th, td { padding:10px 8px; border-bottom:1px solid var(--border); text-align:left; vertical-align:top; }
    th { color:#374151; background:#f9fafb; position:sticky; top:0; z-index:1; }
    .table-wrap { overflow:auto; max-height:560px; border:1px solid var(--border); border-radius:12px; }
    .muted { color:var(--muted); font-size:13px; }
    .pill { display:inline-flex; padding:3px 8px; border-radius:999px; font-size:12px; background:#e5e7eb; }
    .pill.ok { background:#dcfce7; color:#166534; }
    .pill.bad { background:#fee2e2; color:#991b1b; }
    .actions { display:flex; flex-wrap:wrap; gap:6px; }
    .hidden { display:none !important; }
    .toast { position:fixed; right:22px; bottom:22px; background:#111827; color:#fff; padding:12px 14px; border-radius:12px; box-shadow:0 8px 24px rgba(0,0,0,.22); max-width:420px; z-index:99; }
    .modal-mask { position:fixed; inset:0; background:rgba(17,24,39,.45); display:flex; align-items:center; justify-content:center; z-index:90; }
    .modal { width:min(960px, calc(100vw - 40px)); max-height:82vh; overflow:auto; background:#fff; border-radius:16px; padding:18px; box-shadow:0 16px 60px rgba(0,0,0,.25); }
    .modal-head { display:flex; justify-content:space-between; align-items:center; gap:12px; margin-bottom:12px; }
    .modal-head h3 { margin:0; }
    code { background:#f3f4f6; padding:2px 5px; border-radius:6px; }
    @media (max-width: 900px) { .grid { grid-template-columns:1fr 1fr; } .grid .span2,.grid .span3 { grid-column: span 2; } }
  </style>
</head>
<body>
  <header>
    <h1>授权管理后台 <span class="muted" style="color:#d1d5db">V1.1</span></h1>
    <div class="right">
      <span id="loginUser" class="muted" style="color:#d1d5db"></span>
      <button class="secondary" onclick="logout()">退出</button>
    </div>
  </header>

  <main>
    <section id="loginBox" class="card login hidden">
      <h2 style="margin-top:0">管理员登录</h2>
      <p class="muted">使用 <code>.env</code> 中的 ADMIN_USERNAME / ADMIN_PASSWORD 登录。</p>
      <div style="margin-bottom:12px">
        <label>用户名</label>
        <input id="username" value="admin" autocomplete="username" />
      </div>
      <div style="margin-bottom:16px">
        <label>密码</label>
        <input id="password" type="password" value="admin123456" autocomplete="current-password" onkeydown="if(event.key==='Enter') login()" />
      </div>
      <button onclick="login()">登录</button>
    </section>

    <section id="appBox" class="hidden">
      <div class="tabs">
        <button id="tabLicenses" class="active" onclick="switchTab('licenses')">卡密管理</button>
        <button id="tabLogs" onclick="switchTab('logs')">激活日志</button>
      </div>

      <section id="licensesPanel">
        <div class="card">
          <h2 style="margin-top:0">创建卡密</h2>
          <div class="grid">
            <div><label>数量</label><input id="count" type="number" min="1" max="500" value="1" /></div>
            <div><label>产品编号</label><input id="productCode" value="default" /></div>
            <div><label>套餐</label><input id="plan" value="standard" /></div>
            <div><label>最大设备数</label><input id="maxDevices" type="number" min="1" max="100" value="1" /></div>
            <div><label>有效天数</label><input id="expireDays" type="number" min="1" value="365" /></div>
            <div class="span2"><label>备注</label><input id="note" placeholder="例如：订单号 / 客户名" /></div>
            <div><button onclick="createLicenses()">创建</button></div>
          </div>
        </div>

        <div class="card">
          <div style="display:flex; justify-content:space-between; align-items:center; gap:12px; margin-bottom:12px">
            <h2 style="margin:0">卡密列表</h2>
            <button class="ghost" onclick="loadLicenses()">刷新</button>
          </div>
          <div class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>ID</th><th>卡密</th><th>产品</th><th>套餐</th><th>设备</th><th>过期时间</th><th>状态</th><th>备注</th><th>创建时间</th><th>操作</th>
                </tr>
              </thead>
              <tbody id="licenseRows"></tbody>
            </table>
          </div>
        </div>
      </section>

      <section id="logsPanel" class="hidden">
        <div class="card">
          <div style="display:flex; justify-content:space-between; align-items:center; gap:12px; margin-bottom:12px">
            <h2 style="margin:0">激活 / 校验日志</h2>
            <button class="ghost" onclick="loadLogs()">刷新</button>
          </div>
          <div class="table-wrap">
            <table>
              <thead><tr><th>ID</th><th>卡密</th><th>设备指纹</th><th>IP</th><th>动作</th><th>结果</th><th>消息</th><th>时间</th></tr></thead>
              <tbody id="logRows"></tbody>
            </table>
          </div>
        </div>
      </section>
    </section>
  </main>

  <div id="modalMask" class="modal-mask hidden">
    <div class="modal">
      <div class="modal-head">
        <h3 id="modalTitle">详情</h3>
        <button class="secondary" onclick="closeModal()">关闭</button>
      </div>
      <div id="modalBody"></div>
    </div>
  </div>

  <div id="toast" class="toast hidden"></div>

<script>
const API = '/api/v1/admin';
let token = localStorage.getItem('admin_token') || '';
let currentTab = 'licenses';

function esc(v) {
  return String(v ?? '').replace(/[&<>'"]/g, s => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[s]));
}
function fmt(ts) {
  if (!ts) return '-';
  return new Date(ts * 1000).toLocaleString();
}
function toast(msg) {
  const el = document.getElementById('toast');
  el.textContent = msg;
  el.classList.remove('hidden');
  setTimeout(() => el.classList.add('hidden'), 2600);
}
async function request(path, options = {}) {
  const headers = Object.assign({'Content-Type': 'application/json'}, options.headers || {});
  if (token) headers.Authorization = 'Bearer ' + token;
  const res = await fetch(API + path, Object.assign({}, options, {headers}));
  const data = await res.json().catch(() => ({code: res.status, msg: '响应不是 JSON'}));
  if (data.code !== 0) throw new Error(data.msg || '请求失败');
  return data.data || {};
}
function showLogin() {
  document.getElementById('loginBox').classList.remove('hidden');
  document.getElementById('appBox').classList.add('hidden');
  document.querySelector('header .right').classList.add('hidden');
}
function showApp() {
  document.getElementById('loginBox').classList.add('hidden');
  document.getElementById('appBox').classList.remove('hidden');
  document.querySelector('header .right').classList.remove('hidden');
  document.getElementById('loginUser').textContent = '已登录';
}
async function login() {
  try {
    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value;
    const res = await fetch(API + '/login', {
      method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({username, password})
    });
    const data = await res.json();
    if (data.code !== 0) throw new Error(data.msg || '登录失败');
    token = data.data.token;
    localStorage.setItem('admin_token', token);
    showApp();
    loadLicenses();
  } catch (e) { toast(e.message); }
}
function logout() {
  token = '';
  localStorage.removeItem('admin_token');
  showLogin();
}
function switchTab(tab) {
  currentTab = tab;
  document.getElementById('tabLicenses').classList.toggle('active', tab === 'licenses');
  document.getElementById('tabLogs').classList.toggle('active', tab === 'logs');
  document.getElementById('licensesPanel').classList.toggle('hidden', tab !== 'licenses');
  document.getElementById('logsPanel').classList.toggle('hidden', tab !== 'logs');
  if (tab === 'logs') loadLogs(); else loadLicenses();
}
async function createLicenses() {
  try {
    const payload = {
      count: Number(document.getElementById('count').value || 1),
      productCode: document.getElementById('productCode').value.trim() || 'default',
      plan: document.getElementById('plan').value.trim() || 'standard',
      maxDevices: Number(document.getElementById('maxDevices').value || 1),
      expireDays: Number(document.getElementById('expireDays').value || 365),
      note: document.getElementById('note').value.trim() || null,
    };
    const data = await request('/licenses', {method:'POST', body: JSON.stringify(payload)});
    showModal('新建卡密', '<p class="muted">已创建 ' + data.keys.length + ' 个卡密：</p><textarea readonly style="height:180px">' + esc(data.keys.join('\n')) + '</textarea>');
    loadLicenses();
  } catch (e) { toast(e.message); }
}
async function loadLicenses() {
  try {
    const data = await request('/licenses');
    const rows = data.items || [];
    document.getElementById('licenseRows').innerHTML = rows.map(x => `
      <tr>
        <td>${x.id}</td>
        <td><code>${esc(x.licenseKey)}</code></td>
        <td>${esc(x.productCode)}</td>
        <td>${esc(x.plan)}</td>
        <td>${x.activeDevices}/${x.maxDevices}</td>
        <td>${fmt(x.expireAt)}</td>
        <td>${x.isActive ? '<span class="pill ok">启用</span>' : '<span class="pill bad">禁用</span>'}</td>
        <td>${esc(x.note || '')}</td>
        <td>${fmt(x.createdAt)}</td>
        <td><div class="actions">
          <button class="ghost" onclick="showDevices(${x.id}, '${esc(x.licenseKey)}')">设备</button>
          <button class="ghost" onclick="extendLicense(${x.id})">续期</button>
          ${x.isActive ? `<button class="danger" onclick="disableLicense(${x.id})">禁用</button>` : `<button class="ok" onclick="enableLicense(${x.id})">启用</button>`}
        </div></td>
      </tr>`).join('');
  } catch (e) {
    if (String(e.message).includes('token') || String(e.message).includes('登录')) logout();
    toast(e.message);
  }
}
async function disableLicense(id) {
  if (!confirm('确定禁用该卡密？')) return;
  try { await request(`/licenses/${id}/disable`, {method:'POST'}); toast('已禁用'); loadLicenses(); } catch(e) { toast(e.message); }
}
async function enableLicense(id) {
  try { await request(`/licenses/${id}/enable`, {method:'POST'}); toast('已启用'); loadLicenses(); } catch(e) { toast(e.message); }
}
async function extendLicense(id) {
  const days = Number(prompt('请输入续期天数', '365'));
  if (!days) return;
  try { await request(`/licenses/${id}/extend`, {method:'POST', body:JSON.stringify({days})}); toast('已续期'); loadLicenses(); } catch(e) { toast(e.message); }
}
async function showDevices(id, key) {
  try {
    const data = await request(`/licenses/${id}/devices`);
    const rows = data.items || [];
    const html = `<p class="muted">卡密：<code>${esc(key)}</code></p><div class="table-wrap"><table><thead><tr><th>ID</th><th>主机</th><th>平台</th><th>版本</th><th>设备指纹</th><th>首次激活</th><th>最后校验</th><th>状态</th><th>操作</th></tr></thead><tbody>` +
      rows.map(d => `<tr><td>${d.id}</td><td>${esc(d.hostname || '')}</td><td>${esc((d.platform || '') + ' ' + (d.arch || ''))}</td><td>${esc(d.appVersion || '')}</td><td><code>${esc(d.machineFingerprint || '')}</code></td><td>${fmt(d.firstActivatedAt)}</td><td>${fmt(d.lastSeenAt)}</td><td>${d.isRevoked ? '<span class="pill bad">已解绑</span>' : '<span class="pill ok">正常</span>'}</td><td>${d.isRevoked ? '-' : `<button class="danger" onclick="revokeDevice(${d.id}, ${id}, '${esc(key)}')">解绑</button>`}</td></tr>`).join('') +
      `</tbody></table></div>`;
    showModal('绑定设备', html);
  } catch(e) { toast(e.message); }
}
async function revokeDevice(deviceId, licenseId, key) {
  if (!confirm('确定解绑该设备？解绑后该设备无法继续在线校验。')) return;
  try { await request(`/devices/${deviceId}/revoke`, {method:'POST'}); toast('已解绑'); await showDevices(licenseId, key); loadLicenses(); } catch(e) { toast(e.message); }
}
async function loadLogs() {
  try {
    const data = await request('/logs');
    const rows = data.items || [];
    document.getElementById('logRows').innerHTML = rows.map(x => `<tr><td>${x.id}</td><td><code>${esc(x.licenseKey || '')}</code></td><td><code>${esc(x.machineFingerprint || '')}</code></td><td>${esc(x.ip || '')}</td><td>${esc(x.action)}</td><td>${x.success ? '<span class="pill ok">成功</span>' : '<span class="pill bad">失败</span>'}</td><td>${esc(x.message || '')}</td><td>${fmt(x.createdAt)}</td></tr>`).join('');
  } catch(e) { toast(e.message); }
}
function showModal(title, html) {
  document.getElementById('modalTitle').textContent = title;
  document.getElementById('modalBody').innerHTML = html;
  document.getElementById('modalMask').classList.remove('hidden');
}
function closeModal() { document.getElementById('modalMask').classList.add('hidden'); }

if (token) { showApp(); loadLicenses(); } else { showLogin(); }
</script>
</body>
</html>
'''


@router.get("/admin", response_class=HTMLResponse)
def admin_page():
    return HTMLResponse(ADMIN_HTML)


@router.get("/admin/", response_class=HTMLResponse)
def admin_page_slash():
    return HTMLResponse(ADMIN_HTML)
