const axios = require('axios');

const AUTH_SERVER = process.env.AUTH_SERVER || 'http://127.0.0.1:8000/api/v1';

async function activateLicense(payload) {
  const res = await axios.post(`${AUTH_SERVER}/license/activate`, payload, { timeout: 10000 });
  return res.data;
}

async function verifyLicense(payload) {
  const res = await axios.post(`${AUTH_SERVER}/license/verify`, payload, { timeout: 10000 });
  return res.data;
}

module.exports = { activateLicense, verifyLicense, AUTH_SERVER };
