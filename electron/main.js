const { app, BrowserWindow, Menu } = require('electron');
const path = require('path');
const http = require('http');
const https = require('https');
const { spawn } = require('child_process');

// Configuration
const FLASK_URL = 'https://desktop-sms.onrender.com';
const RETRY_INTERVAL = 2000; // 2 seconds between checks (better for cloud)
const MAX_RETRIES = 60;      // max 2 minutes of waiting for Render spin-up

let mainWindow = null;
let backendProcess = null;

// Determine if running in production (packaged) or development
const isDev = !app.isPackaged;

function startBackend() {
    // We are using a cloud backend on Render, so we don't need to start a local one.
    console.log('Using cloud backend at:', FLASK_URL);
    return;
}

function stopBackend() {
    if (backendProcess) {
        console.log('Stopping backend process...');
        backendProcess.kill();
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
}

/**
 * Polls the Flask backend until it responds,
 * then calls the callback.
 */
function waitForFlask(callback, retries = 0) {
    const client = FLASK_URL.startsWith('https') ? https : http;

    const req = client.get(FLASK_URL, (res) => {
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
                ? `Could not connect to the Flask backend at ${FLASK_URL}.\n\nPlease ensure the Flask server is running:\n  .venv\\Scripts\\python run.py`
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
