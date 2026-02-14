# YabaTech JSS Deployment Guide

This document provides step-by-step instructions for deploying the YabaTech JSS Student Management System. 

There are two main ways to deploy/distribute this app:
1.  **Hybrid Cloud Deployment**: Backend on Render, Database on Supabase, and Electron Deskstop App on user machines. (Recommended for multi-device access).
2.  **Standalone Local Deployment**: Packaged as a single `.exe` that runs offline (using your local Python environment).

---

## 1. Database Setup (Supabase)
Before any deployment, your database must be ready.

1.  **Create Project**: Go to [Supabase](https://supabase.com/) and create a new project.
2.  **Initialize Schema**:
    *   Open the **SQL Editor** in the Supabase dashboard.
    *   Copy the contents of `supabase_setup.sql` from the project root.
    *   Paste it into the SQL Editor and click **Run**.
3.  **Get Credentials**:
    *   Go to **Project Settings > API**.
    *   Copy the **Project URL** and **anon public Key**.

---

## 2. Backend Deployment (Render)
To host the Flask API so it's accessible over the internet:

1.  **GitHub Upload**:
    *   Initialize a git repo: `git init`
    *   Commit files: `git add .` then `git commit -m "initial commit"`
    *   Push to your GitHub repository.
2.  **Create Render Web Service**:
    *   Log in to [Render](https://render.com/).
    *   Click **New + > Web Service**.
    *   Connect your GitHub repository.
3.  **Configure Service**:
    *   **Runtime**: Python 3
    *   **Build Command**: `pip install -r requirements.txt`
    *   **Start Command**: `gunicorn run:app`
4.  **Environment Variables**:
    *   In Render's **Environment** tab, add:
        *   `SUPABASE_URL`: (Your Supabase URL)
        *   `SUPABASE_KEY`: (Your Supabase Key)
        *   `SECRET_KEY`: (Any random string)
5.  **Copy URL**: Once deployed, copy your Render URL (e.g., `https://yabatech-backend.onrender.com`).

---

## 3. Desktop App Configuration (Electron)
Once your backend is live on Render, you need to point the Electron app to it.

1.  Open `electron/main.js`.
2.  Find the `FLASK_URL` constant:
    ```javascript
    const FLASK_URL = 'https://your-app-name.onrender.com'; // Replace with Render URL
    ```
3.  In the `startBackend()` function, ensure it returns early so it doesn't try to start a local server:
    ```javascript
    function startBackend() {
        return; // Skip local backend since we are using Render
    }
    ```

---

## 4. Packaging the Desktop App (.exe)
To create a folder you can send to school computers:

### Method A: Using the Automated Script (Local Bundle)
If you want to bundle the Python backend *inside* the exe (works offline):
1.  Ensure you have your virtual environment active and all `requirements.txt` installed.
2.  Run the build batch file:
    ```bash
    .\build_installer.bat
    ```
3.  The output will be in `electron/dist/YabaTech School Manager-win32-x64/`.

### Method B: Manual Packaging (Cloud Backend)
If you are using the Render backend:
1.  Navigate to the electron folder: `cd electron`
2.  Install dependencies: `npm install`
3.  Package the app:
    ```bash
    npx @electron/packager . "YabaTech School Manager" --platform=win32 --arch=x64 --out=dist --overwrite
    ```
4.  Distribute the resulting folder in `electron/dist/`.

---

## 5. Summary Checklists

### Production Environment Variables (.env)
Your `.env` file should look like this (but don't upload it to GitHub!):
```env
SUPABASE_URL=https://xyz.supabase.co
SUPABASE_KEY=your-api-key
SECRET_KEY=highly-secret-string
```

### Common Issues
*   **CORS**: Render might block requests from Electron. Ensure Flask-CORS is installed if you encounter login issues.
*   **Cold Starts**: Render's free tier sleeps. If the app shows a "Connection Error" on startup, wait 1 minute for Render to wake up and try again.
