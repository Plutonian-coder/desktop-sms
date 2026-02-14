const { app, BrowserWindow, Menu } = require('electron');
const path = require('path');
const http = require('http');
const { spawn } = require('child_process');

// Configuration
const FLASK_URL = 'http://127.0.0.1:5000';
const RETRY_INTERVAL = 500; // ms between connection checks
const MAX_RETRIES = 60;     // max ~30 seconds of waiting

let mainWindow = null;
let backendProcess = null;

// Determine if running in production (packaged) or development
const isDev = !app.isPackaged;

function startBackend() {
    if (isDev) {
        console.log('Development mode: Please start Flask manually with "python run.py"');
        return;
    }

    // Production mode: spawn the bundled backend executable
    const backendPath = path.join(process.resourcesPath, 'yabatech_backend.exe');
    console.log('Starting backend from:', backendPath);

    backendProcess = spawn(backendPath, [], {
        cwd: path.dirname(backendPath),
        stdio: 'inherit'
    });

    backendProcess.on('error', (err) => {
        console.error('Failed to start backend:', err);
    });

    backendProcess.on('exit', (code) => {
        console.log(`Backend process exited with code ${code}`);
    });
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
