const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { app } = require('electron');
const { machineIdSync } = require('node-machine-id');

const LICENSE_FILE = path.join(app.getPath('userData'), 'license.dat');
const CLIENT_STORAGE_SECRET = 'change-this-client-storage-obfuscation-secret-before-release';

function getKey() {
  let machineId = 'unknown-machine';
  try {
    machineId = machineIdSync();
  } catch (_) {}
  return crypto.createHash('sha256').update(CLIENT_STORAGE_SECRET + '::' + machineId).digest();
}

function encrypt(text) {
  const iv = crypto.randomBytes(16);
  const cipher = crypto.createCipheriv('aes-256-cbc', getKey(), iv);
  let encrypted = cipher.update(text, 'utf8', 'hex');
  encrypted += cipher.final('hex');
  return iv.toString('hex') + ':' + encrypted;
}

function decrypt(text) {
  const parts = String(text || '').split(':');
  if (parts.length !== 2) throw new Error('invalid license file');
  const iv = Buffer.from(parts[0], 'hex');
  const decipher = crypto.createDecipheriv('aes-256-cbc', getKey(), iv);
  let decrypted = decipher.update(parts[1], 'hex', 'utf8');
  decrypted += decipher.final('utf8');
  return decrypted;
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

module.exports = { saveLicenseToken, loadLicenseToken, clearLicenseToken };
