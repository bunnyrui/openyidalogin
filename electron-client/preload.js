'use strict';

const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('yida', {
  onStatus: (callback) => ipcRenderer.on('status', (_event, data) => callback(data)),
  manualSave: () => ipcRenderer.invoke('manual-save'),
  openResultFolder: () => ipcRenderer.invoke('open-result-folder'),
  reloadLogin: () => ipcRenderer.invoke('reload-login'),
  clearSession: () => ipcRenderer.invoke('clear-session'),

  // 授权相关 API：沿用原来 renderer.js 的调用方式，但底层改为 V1.1 licenseToken 授权
  verifyKey: (key) => ipcRenderer.invoke('verify-key', key),
  checkSavedAuth: () => ipcRenderer.invoke('check-saved-auth'),
  clearLocalAuth: () => ipcRenderer.invoke('clear-local-auth')
});
