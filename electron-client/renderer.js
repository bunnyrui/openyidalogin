'use strict';

const statusEl = document.getElementById('status');
const openFolderBtn = document.getElementById('openFolder');
const manualSaveBtn = document.getElementById('manualSave');
const reloadBtn = document.getElementById('reload');
const clearBtn = document.getElementById('clear');

const authPanel = document.getElementById('auth-panel');
const mainPanel = document.getElementById('main-panel');
const verifyBtn = document.getElementById('verifyBtn');
const licenseInput = document.getElementById('licenseKey');
const authError = document.getElementById('auth-error');

function setStatus(data) {
  statusEl.className = 'status ' + (data.type || 'info');
  let message = data.message || '';
  if (data.extra && data.extra.outputFile) {
    message += '\n\n文件位置：' + data.extra.outputFile;
  }
  statusEl.textContent = message;
}

window.yida.onStatus(setStatus);

function showMainPanel() {
  authPanel.style.display = 'none';
  mainPanel.style.display = 'block';
}

window.addEventListener('DOMContentLoaded', async () => {
  verifyBtn.innerText = '正在检查授权...';
  verifyBtn.disabled = true;
  
  const isAuth = await window.yida.checkSavedAuth();
  
  if (isAuth) {
    showMainPanel();
  } else {
    verifyBtn.innerText = '验证并激活';
    verifyBtn.disabled = false;
  }
});

verifyBtn.addEventListener('click', async () => {
  const key = licenseInput.value.trim();
  if (!key) {
    authError.textContent = '请输入授权码！';
    authError.style.display = 'block';
    return;
  }

  verifyBtn.innerText = '验证中...';
  verifyBtn.disabled = true;
  authError.style.display = 'none';

  const result = await window.yida.verifyKey(key);

  if (result.success) {
    showMainPanel();
  } else {
    authError.textContent = result.message;
    authError.style.display = 'block';
    verifyBtn.innerText = '验证并激活';
    verifyBtn.disabled = false;
  }
});

openFolderBtn.addEventListener('click', async () => {
  await window.yida.openResultFolder();
});

manualSaveBtn.addEventListener('click', async () => {
  try {
    const file = await window.yida.manualSave();
    setStatus({ type: 'success', message: '已手动保存。', extra: { outputFile: file } });
  } catch (err) {
    setStatus({ type: 'error', message: '手动保存失败：' + (err && err.message ? err.message : String(err)) });
  }
});

reloadBtn.addEventListener('click', async () => {
  await window.yida.reloadLogin();
});

clearBtn.addEventListener('click', async () => {
  await window.yida.clearSession();
});