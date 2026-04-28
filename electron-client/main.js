'use strict';

const { app, BrowserWindow, BrowserView, ipcMain, shell, dialog } = require('electron');
const fs = require('fs');
const path = require('path');
const os = require('os');

const { checkLocalLicense, verifyOnlineSilently } = require('./src/auth/authGuard');
const { activateLicense } = require('./src/auth/authClient');
const { getMachineFingerprint, getMachineInfo } = require('./src/auth/machine');
const { saveLicenseToken, clearLicenseToken } = require('./src/auth/localLicense');

// ================= 配置参数 =================
const LOGIN_URL = process.env.YIDA_LOGIN_URL || 'https://www.aliwork.com/workPlatform';
const DEFAULT_BASE_URL = process.env.YIDA_BASE_URL || 'https://www.aliwork.com';
const RESULT_DIR_NAME = 'yida-login-result';

let mainWindow;
let loginView;
let timer;
let lastSavedFile = '';
let yidaLoaded = false;

// ================= 工具函数 =================
function getDesktopDir() {
  return app.getPath('desktop') || path.join(os.homedir(), 'Desktop');
}

function getOutputFile() {
  const outputDir = path.join(getDesktopDir(), RESULT_DIR_NAME, '.cache');
  return path.join(outputDir, 'cookies-public.json');
}

function isUsefulCookie(cookie) {
  const domain = cookie.domain || '';
  return domain.includes('aliwork.com') || domain.includes('dingtalk.com') || domain.includes('login.dingtalk.com');
}

function hasLoginCookie(cookies) {
  return cookies.some((cookie) => {
    return cookie.name === 'tianshu_csrf_token' && cookie.value && (cookie.domain || '').includes('aliwork.com');
  });
}

function normalizeCookie(cookie) {
  return {
    name: cookie.name,
    value: cookie.value,
    domain: cookie.domain,
    path: cookie.path || '/',
    expires: typeof cookie.expirationDate === 'number' ? cookie.expirationDate : -1,
    httpOnly: !!cookie.httpOnly,
    secure: !!cookie.secure,
    sameSite: cookie.sameSite || 'Lax'
  };
}

function resolveBaseUrl(cookies, currentUrl) {
  const yidaCookie = cookies.find((cookie) => {
    return cookie.name === 'yida_user_cookie' && (cookie.domain || '').includes('aliwork.com');
  });

  if (yidaCookie && yidaCookie.domain) {
    return 'https://' + yidaCookie.domain.replace(/^\./, '');
  }

  try {
    return new URL(currentUrl).origin;
  } catch (err) {
    return DEFAULT_BASE_URL;
  }
}

function sendStatus(type, message, extra) {
  if (!mainWindow || mainWindow.isDestroyed()) return;
  mainWindow.webContents.send('status', { type, message, extra: extra || null });
}

// ================= 宜搭 Cookie 获取核心逻辑 =================
async function getAllCookies() {
  if (!loginView) return [];
  return loginView.webContents.session.cookies.get({});
}

async function saveCookies() {
  const allCookies = await getAllCookies();
  const filtered = allCookies.filter(isUsefulCookie).map(normalizeCookie);
  const currentUrl = loginView.webContents.getURL();
  const baseUrl = resolveBaseUrl(filtered, currentUrl);

  const outputFile = getOutputFile();
  fs.mkdirSync(path.dirname(outputFile), { recursive: true });
  fs.writeFileSync(outputFile, JSON.stringify({ cookies: filtered, base_url: baseUrl }, null, 2), 'utf8');

  lastSavedFile = outputFile;
  return outputFile;
}

async function checkAndSave() {
  try {
    const allCookies = await getAllCookies();

    if (!hasLoginCookie(allCookies)) {
      return false;
    }

    const outputFile = await saveCookies();
    sendStatus('success', '登录态已生成成功。', { outputFile });

    if (timer) {
      clearInterval(timer);
      timer = null;
    }

    return true;
  } catch (err) {
    sendStatus('error', '保存登录态失败：' + (err && err.message ? err.message : String(err)));
    return false;
  }
}

function layoutViews() {
  if (!mainWindow || !loginView) return;

  const bounds = mainWindow.getContentBounds();
  const sidebarWidth = 360;

  loginView.setBounds({
    x: sidebarWidth,
    y: 0,
    width: Math.max(640, bounds.width - sidebarWidth),
    height: bounds.height
  });

  loginView.setAutoResize({ width: true, height: true });
}

async function loadYidaPage() {
  if (!loginView) return;

  yidaLoaded = true;
  layoutViews();

  sendStatus('info', '正在打开宜搭登录页面，请在右侧窗口使用钉钉扫码登录。');

  try {
    await loginView.webContents.loadURL(LOGIN_URL);
  } catch (err) {
    // Electron 页面跳转/重定向经常会抛 ERR_ABORTED，这种可以忽略
    if (err.code !== 'ERR_ABORTED' && err.errno !== -3) {
      console.error('页面加载失败:', err);
      sendStatus('error', '宜搭页面加载失败：' + (err && err.message ? err.message : String(err)));
    }
  }

  if (timer) clearInterval(timer);
  timer = setInterval(checkAndSave, 2000);
}

// ================= 授权逻辑：V1.1 licenseToken =================
async function checkSavedAuthAndLoadYida() {
  const local = checkLocalLicense();

  if (!local.valid) {
    return false;
  }

  // 有本地有效授权时，先进入软件；在线校验失败不阻断离线使用
  await loadYidaPage();

  verifyOnlineSilently()
    .then((online) => {
      if (online && online.valid === false) {
        clearLicenseToken();
        sendStatus('error', '在线授权校验失败：' + (online.reason || '授权已失效，请重新激活。'));
      }
    })
    .catch(() => {});

  return true;
}

// 1. 启动时自动检查本地授权
ipcMain.handle('check-saved-auth', async () => {
  return checkSavedAuthAndLoadYida();
});

// 2. 验证用户输入的 Key，并在成功后打开宜搭页面
ipcMain.handle('verify-key', async (_event, key) => {
  try {
    const licenseKey = String(key || '').trim();

    if (!licenseKey) {
      return { success: false, message: '请输入授权码。' };
    }

    const machineFingerprint = getMachineFingerprint();
    const machineInfo = getMachineInfo();

    const result = await activateLicense({
      licenseKey,
      machineFingerprint,
      ...machineInfo
    });

    if (result.code === 0 && result.data && result.data.licenseToken) {
      saveLicenseToken(result.data.licenseToken);
      await loadYidaPage();
      return { success: true };
    }

    return {
      success: false,
      message: result && result.msg ? result.msg : '授权码无效或已超过绑定设备数量。'
    };
  } catch (err) {
    console.error('请求验证服务器失败:', err);
    return {
      success: false,
      message: '无法连接验证服务器：' + (err && err.message ? err.message : String(err))
    };
  }
});

ipcMain.handle('clear-local-auth', async () => {
  clearLicenseToken();
  return true;
});

// ================= 原宜搭工具按钮 =================
ipcMain.handle('manual-save', async () => {
  const outputFile = await saveCookies();
  sendStatus('success', '已手动保存当前 Cookie。', { outputFile });
  return outputFile;
});

ipcMain.handle('open-result-folder', async () => {
  const folder = lastSavedFile ? path.dirname(path.dirname(lastSavedFile)) : path.join(getDesktopDir(), RESULT_DIR_NAME);
  await shell.openPath(folder);
  return folder;
});

ipcMain.handle('reload-login', async () => {
  if (!loginView) return false;

  try {
    await loginView.webContents.loadURL(LOGIN_URL);
  } catch (err) {
    if (err.code !== 'ERR_ABORTED' && err.errno !== -3) {
      console.error('重新加载失败:', err);
    }
  }

  sendStatus('info', '已重新打开宜搭登录页面。');
  return true;
});

ipcMain.handle('clear-session', async () => {
  const response = await dialog.showMessageBox(mainWindow, {
    type: 'warning',
    buttons: ['清空并重新登录', '取消'],
    defaultId: 1,
    cancelId: 1,
    title: '清空登录会话',
    message: '确认清空本工具保存的浏览器会话吗？',
    detail: '这不会影响用户系统中已安装的 Chrome、Edge 或其他浏览器。'
  });

  if (response.response !== 0) return false;

  if (loginView) {
    const ses = loginView.webContents.session;
    await ses.clearStorageData();
    await ses.clearCache();

    try {
      await loginView.webContents.loadURL(LOGIN_URL);
    } catch (err) {
      if (err.code !== 'ERR_ABORTED' && err.errno !== -3) {
        console.error('清空后加载失败:', err);
      }
    }
  }

  sendStatus('info', '已清空本工具会话，请重新扫码登录。');
  return true;
});

// ================= 窗口创建 =================
async function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 860,
    minWidth: 980,
    minHeight: 680,
    title: '宜搭自助登录',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false
    }
  });

  loginView = new BrowserView({
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      partition: 'persist:yida-self-login'
    }
  });

  mainWindow.setBrowserView(loginView);
  layoutViews();

  mainWindow.on('resize', layoutViews);

  loginView.webContents.on('did-navigate', () => checkAndSave());
  loginView.webContents.on('did-navigate-in-page', () => checkAndSave());
  loginView.webContents.on('did-finish-load', () => checkAndSave());

  await mainWindow.loadFile(path.join(__dirname, 'renderer.html'));

  sendStatus('info', '等待授权验证...');
}

app.whenReady().then(createWindow);

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});

app.on('window-all-closed', () => {
  if (timer) clearInterval(timer);
  if (process.platform !== 'darwin') {
    app.quit();
  }
});
