const crypto = require('crypto');
const os = require('os');
const { machineIdSync } = require('node-machine-id');
const pkg = require('../../package.json');

function sha256(text) {
  return crypto.createHash('sha256').update(text).digest('hex');
}

function getSafeMachineId() {
  try {
    return machineIdSync();
  } catch (_) {
    return [os.hostname(), os.platform(), os.arch()].join('::');
  }
}

function getMachineFingerprint() {
  const raw = ['machine-v2', getSafeMachineId()].join('::');
  return sha256(raw);
}

function getMachineInfo() {
  return {
    machineId: getSafeMachineId(),
    hostname: os.hostname(),
    platform: os.platform(),
    arch: os.arch(),
    appVersion: pkg.version
  };
}

module.exports = { getMachineFingerprint, getMachineInfo, getSafeMachineId };
