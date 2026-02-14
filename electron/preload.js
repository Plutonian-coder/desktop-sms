// Electron preload script — context isolation bridge
// Minimal preload for security; add IPC bridges here if needed.
const { contextBridge } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
    platform: process.platform,
    isElectron: true,
});
