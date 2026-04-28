'use strict';

const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('yida', {
  onStatus: (callback) => ipcRenderer.on('status', (_event, data) => callback(data)),
  manualSave: () => ipcRenderer.invoke('manual-save'),
  openResultFolder: () => ipcRenderer.invoke('open-result-folder'),
  reloadLogin: () => ipcRenderer.invoke('reload-login'),
  clearSession: () => ipcRenderer.invoke('clear-session'),

  // 授权相关 API
  verifyKey: (key) => ipcRenderer.invoke('verify-key', key),
  checkSavedAuth: () => ipcRenderer.invoke('check-saved-auth'),
  clearLocalAuth: () => ipcRenderer.invoke('clear-local-auth')
});
