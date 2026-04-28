const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { app } = require('electron');
const { machineIdSync } = require('node-machine-id');
const pkg = require('../../package.json');

const LICENSE_FILE = path.join(app.getPath('userData'), 'license.dat');
const LOCAL_DEV_STORAGE_SECRET = 'local-dev-storage-secret';

function getStorageSecret() {
  const configured = String(process.env.CLIENT_STORAGE_SECRET || (pkg.config && pkg.config.storageSecret) || '').trim();

  if (configured) {
    return configured;
  }

  if (app && app.isPackaged) {
    throw new Error('客户端本地授权存储密钥未配置，请在 electron-client/package.json 的 config.storageSecret 中填写随机长字符串后重新打包。');
  }

  return LOCAL_DEV_STORAGE_SECRET;
}

function getKey() {
  let machineId = 'unknown-machine';
  try {
    machineId = machineIdSync();
  } catch (_) {}
  return crypto.createHash('sha256').update(getStorageSecret() + '::' + machineId).digest();
}

function encrypt(text) {
  const iv = crypto.randomBytes(12);
  const cipher = crypto.createCipheriv('aes-256-gcm', getKey(), iv);
  const encrypted = Buffer.concat([cipher.update(text, 'utf8'), cipher.final()]);
  const tag = cipher.getAuthTag();
  return ['v2', iv.toString('hex'), tag.toString('hex'), encrypted.toString('hex')].join(':');
}

function decryptLegacy(text) {
  const parts = String(text || '').split(':');
  if (parts.length !== 2) throw new Error('invalid legacy license file');
  const iv = Buffer.from(parts[0], 'hex');
  const decipher = crypto.createDecipheriv('aes-256-cbc', getKey(), iv);
  let decrypted = decipher.update(parts[1], 'hex', 'utf8');
  decrypted += decipher.final('utf8');
  return decrypted;
}

function decrypt(text) {
  const parts = String(text || '').split(':');
  if (parts[0] !== 'v2') {
    return decryptLegacy(text);
  }
  if (parts.length !== 4) throw new Error('invalid license file');
  const iv = Buffer.from(parts[1], 'hex');
  const tag = Buffer.from(parts[2], 'hex');
  const decipher = crypto.createDecipheriv('aes-256-gcm', getKey(), iv);
  decipher.setAuthTag(tag);
  return Buffer.concat([decipher.update(parts[3], 'hex'), decipher.final()]).toString('utf8');
}

function saveLicenseToken(token) {
  fs.mkdirSync(path.dirname(LICENSE_FILE), { recursive: true });
  fs.writeFileSync(LICENSE_FILE, encrypt(token), 'utf8');
}

function loadLicenseToken() {
  if (!fs.existsSync(LICENSE_FILE)) return null;
  try {
    return decrypt(fs.readFileSync(LICENSE_FILE, 'utf8'));
  } catch (_) {
    return null;
  }
}

function clearLicenseToken() {
  if (fs.existsSync(LICENSE_FILE)) fs.unlinkSync(LICENSE_FILE);
}

module.exports = { saveLicenseToken, loadLicenseToken, clearLicenseToken, getStorageSecret };
