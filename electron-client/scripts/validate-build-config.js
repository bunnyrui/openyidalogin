#!/usr/bin/env node
'use strict';

const pkg = require('../package.json');

function value(name, envName) {
  return String(process.env[envName] || (pkg.config && pkg.config[name]) || '').trim();
}

const missing = [];
if (!value('authServer', 'AUTH_SERVER')) missing.push('config.authServer or AUTH_SERVER');
if (!value('storageSecret', 'CLIENT_STORAGE_SECRET')) missing.push('config.storageSecret or CLIENT_STORAGE_SECRET');

if (missing.length > 0) {
  console.error('Client build configuration is incomplete.');
  console.error('Missing: ' + missing.join(', '));
  console.error('Set these values in electron-client/package.json or pass environment variables before building.');
  process.exit(1);
}

console.log('Client build configuration ok.');
