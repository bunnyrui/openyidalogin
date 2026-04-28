const crypto = require('crypto');
const os = require('os');
const { machineIdSync } = require('node-machine-id');
const pkg = require('../../package.json');

function sha256(text) {
  return crypto.createHash('sha256').update(text).digest('hex');
}

function getMacList() {
  const nets = os.networkInterfaces();
  const list = [];
  Object.keys(nets).forEach((name) => {
    nets[name].forEach((net) => {
      if (!net.internal && net.mac && net.mac !== '00:00:00:00:00:00') {
        list.push(net.mac);
      }
    });
  });
  return list.sort();
}

function getMachineFingerprint() {
  const cpus = os.cpus();
  const raw = [
    machineIdSync(),
    os.hostname(),
    os.platform(),
    os.arch(),
    cpus && cpus.length ? cpus[0].model : '',
    getMacList().join('|')
  ].join('::');
  return sha256(raw);
}

function getMachineInfo() {
  return {
    machineId: machineIdSync(),
    hostname: os.hostname(),
    platform: os.platform(),
    arch: os.arch(),
    appVersion: pkg.version
  };
}

module.exports = { getMachineFingerprint, getMachineInfo };
