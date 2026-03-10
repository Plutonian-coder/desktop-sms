const { app, BrowserWindow, Menu, session } = require('electron');
const path = require('path');
const http = require('http');
const { spawn, execSync } = require('child_process');

// Determine if running in production (packaged) or development
const isDev = !app.isPackaged;

// Configuration — always local, never cloud
const FLASK_URL = 'http://127.0.0.1:5000';
const RETRY_INTERVAL = 1000; // 1 second between checks
const MAX_RETRIES = 30;      // max 30 seconds of waiting

let mainWindow = null;
let backendProcess = null;

function startBackend() {
    if (isDev) {
        console.log('Dev mode — start Flask manually: python run.py');
        return;
    }

    // Production: launch the bundled Flask executable from resources
    const exePath = path.join(process.resourcesPath, 'yabatech_backend', 'yabatech_backend.exe');
    console.log('Starting backend from:', exePath);

    backendProcess = spawn(exePath, [], {
        stdio: 'ignore',
        windowsHide: true,
        cwd: path.join(process.resourcesPath, 'yabatech_backend'),
    });

    backendProcess.on('error', (err) => {
        console.error('Failed to start backend:', err);
    });

    backendProcess.on('exit', (code) => {
        console.log('Backend exited with code:', code);
    });
}

function stopBackend() {
    if (backendProcess) {
        console.log('Stopping backend process...');
        try {
            // Kill the process tree on Windows (the exe may spawn child processes)
            execSync(`taskkill /pid ${backendProcess.pid} /T /F`, { stdio: 'ignore' });
        } catch (e) {
            // Fallback: try normal kill
            backendProcess.kill();
        }
        backendProcess = null;
    }
}

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1280,
        height: 800,
        minWidth: 1024,
        minHeight: 600,
        title: 'YabaTech School Manager',
        icon: path.join(__dirname, 'icon.png'),
        webPreferences: {
            preload: path.join(__dirname, 'preload.js'),
            contextIsolation: true,
            nodeIntegration: false,
        },
        backgroundColor: '#F2F5F3',
        show: false, // show after ready
    });

    // Remove default menu bar
    Menu.setApplicationMenu(null);

    // Wait for Flask backend before loading
    waitForFlask(() => {
        mainWindow.loadURL(FLASK_URL);
        mainWindow.once('ready-to-show', () => {
            mainWindow.show();
        });
    });

    mainWindow.on('closed', () => {
        mainWindow = null;
    });

    // Allow external images (Google Drive logos, fonts, etc)
    session.defaultSession.webRequest.onHeadersReceived((details, callback) => {
        callback({
            responseHeaders: {
                ...details.responseHeaders,
                'Content-Security-Policy': [
                    "default-src 'self' 'unsafe-inline' 'unsafe-eval' https:; " +
                    "img-src 'self' data: https: blob:; " +
                    "font-src 'self' https://fonts.gstatic.com https://fonts.googleapis.com; " +
                    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdnjs.cloudflare.com; " +
                    "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net;"
                ]
            }
        });
    });
}

/**
 * Polls the Flask backend until it responds,
 * then calls the callback.
 */
function waitForFlask(callback, retries = 0) {
    const req = http.get(FLASK_URL, (res) => {
        // Flask is up
        callback();
    });

    req.on('error', () => {
        if (retries < MAX_RETRIES) {
            setTimeout(() => waitForFlask(callback, retries + 1), RETRY_INTERVAL);
        } else {
            // Flask didn't start — show error
            const { dialog } = require('electron');
            const errorMessage = isDev
                ? `Could not connect to the Flask backend at ${FLASK_URL}.\n\nPlease ensure the Flask server is running:\n  python run.py`
                : `Could not start the application backend.\n\nPlease try restarting the application.`;

            dialog.showErrorBox('Connection Error', errorMessage);
            app.quit();
        }
    });

    req.end();
}

// ── App Lifecycle ──

app.whenReady().then(() => {
    startBackend();
    createWindow();
});

app.on('window-all-closed', () => {
    stopBackend();
    app.quit();
});

app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
        createWindow();
    }
});

app.on('before-quit', () => {
    stopBackend();
});
