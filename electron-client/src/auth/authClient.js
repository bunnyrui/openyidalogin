const axios = require('axios');
const { app } = require('electron');
const pkg = require('../../package.json');

const LOCAL_DEV_AUTH_SERVER = 'http://127.0.0.1:8000/api/v1';

function normalizeBaseUrl(url) {
  return String(url || '').trim().replace(/\/+$/, '');
}

function resolveAuthServer() {
  const configured = normalizeBaseUrl(process.env.AUTH_SERVER || (pkg.config && pkg.config.authServer));

  if (configured) {
    return configured;
  }

  if (app && app.isPackaged) {
    throw new Error('授权服务器地址未配置，请在 electron-client/package.json 的 config.authServer 中填写线上地址后重新打包。');
  }

  return LOCAL_DEV_AUTH_SERVER;
}

function getAuthServer() {
  return resolveAuthServer();
}

async function activateLicense(payload) {
  const res = await axios.post(`${getAuthServer()}/license/activate`, payload, { timeout: 10000 });
  return res.data;
}

async function verifyLicense(payload) {
  const res = await axios.post(`${getAuthServer()}/license/verify`, payload, { timeout: 10000 });
  return res.data;
}

module.exports = { activateLicense, verifyLicense, getAuthServer };
