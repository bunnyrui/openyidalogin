const fs = require('fs');
const path = require('path');
const jwt = require('jsonwebtoken');
const { loadLicenseToken } = require('./localLicense');
const { getMachineFingerprint, getMachineInfo } = require('./machine');
const { verifyLicense } = require('./authClient');

// 生产版：客户端只内置 public.pem，用于验签；private.pem 只放在服务端。
const PUBLIC_KEY_PATH = path.join(__dirname, '..', '..', 'keys', 'public.pem');
const PUBLIC_KEY = fs.readFileSync(PUBLIC_KEY_PATH, 'utf8');

function checkLocalLicense() {
  const token = loadLicenseToken();
  if (!token) return { valid: false, reason: '未激活' };

  try {
    const payload = jwt.verify(token, PUBLIC_KEY, { algorithms: ['RS256'] });
    const now = Math.floor(Date.now() / 1000);

    if (payload.type !== 'license') {
      return { valid: false, reason: '授权类型错误' };
    }

    if (payload.expireAt && payload.expireAt < now) {
      return { valid: false, reason: '授权已过期' };
    }

    if (payload.machineFingerprint !== getMachineFingerprint()) {
      return { valid: false, reason: '设备不匹配' };
    }

    return { valid: true, payload };
  } catch (err) {
    return { valid: false, reason: '授权文件无效', error: err.message };
  }
}

async function verifyOnlineSilently() {
  const token = loadLicenseToken();
  if (!token) return { valid: false, reason: '未激活' };

  try {
    const res = await verifyLicense({
      licenseToken: token,
      machineFingerprint: getMachineFingerprint(),
      appVersion: getMachineInfo().appVersion
    });

    return {
      valid: res && res.code === 0,
      reason: res && res.msg ? res.msg : '',
      response: res
    };
  } catch (err) {
    // 离线策略：服务器不可达时不阻断本地有效授权。
    return { valid: true, offline: true, reason: '在线校验失败，继续使用本地授权' };
  }
}

module.exports = { checkLocalLicense, verifyOnlineSilently };
