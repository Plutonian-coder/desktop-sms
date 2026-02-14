# YabaTech JSS Student Management System

A comprehensive, full-stack school management platform designed for Nigerian Junior Secondary Schools. This system digitizes student registration, academic record-keeping, grading, and automated report card generation.

![Dashboard Preview](assets/dashboard_preview.png) *(Note: Add your own screenshot here)*

## 🚀 Key Features

- **Student Management**: Full registration workflow with validation and class assignment.
- **Academic Setup**: Manage Sessions, Terms, Classes, and Subjects.
- **Dual-Mode Score Entry**:
  - **Student-Centric**: Enter all subjects for a single student.
  - **Subject-Centric**: Enter one subject for the entire class.
- **Automated Ranking Engine**: Calculates positions (subject & class), averages, and class statistics using Pandas.
- **PDF Report Generation**: Professional A4 report cards including academic scores, affective traits, psychomotor skills, and remarks.
- **Cloud Synchronization**: Powered by Supabase (PostgreSQL) for real-time data persistence and multi-device access.
- **Desktop Wrapper**: Built with Electron for a native desktop experience.

## 🛠️ Technology Stack

- **Backend**: Python / Flask
- **Frontend**: HTML5, Vanilla CSS, JavaScript (Jinja2 Templates)
- **Database**: PostgreSQL (via Supabase)
- **Data Processing**: Pandas
- **PDF Generation**: ReportLab
- **Desktop Wrapper**: Electron / Node.js
- **Deployment**: Render (Backend), GitHub Pages / Vercel (Optional Frontend)

## 📁 Project Structure

```text
yabatech_desktop/
├── app/                # Flask Application (Routes, Templates, Static)
├── electron/           # Electron desktop wrapper scripts
├── src/
│   ├── database/       # Supabase Database Manager
│   ├── logic/          # Grading and Ranking engines
│   └── reports/        # PDF Generator (ReportLab)
├── requirements.txt    # Python dependencies
├── run.py              # Flask entry point
├── supabase_setup.sql  # Database schema definition
└── .env                # Environment variables (Supabase URL/Key)
```

## ⚙️ Installation & Setup

### 1. Prerequisites
- Python 3.10+
- Node.js & npm (for Electron)
- A Supabase Account

### 2. Clone the Repository
```bash
git clone https://github.com/your-username/yabatech-jss-management.git
cd yabatech-jss-management
```

### 3. Setup Backend (Flask)
```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 4. Database Configuration
1. Create a new project on [Supabase](https://supabase.com).
2. Run the code in `supabase_setup.sql` in the Supabase SQL Editor to create the necessary tables.
3. Create a `.env` file in the root directory:
   ```env
   SUPABASE_URL=https://your-project-id.supabase.co
   SUPABASE_KEY=your-anon-key
   SECRET_KEY=your-random-secret-key
   ```

### 5. Setup Desktop Wrapper (Electron)
```bash
cd electron
npm install
```

## 🏃 Running the Application

### Development Mode
1. **Start the Flask Server**:
   ```bash
   python run.py
   ```
2. **Start Electron**:
   ```bash
   # In a new terminal
   cd electron
   npm start
   ```

### Production Deployment
- **Backend**: The app is ready for [Render](https://render.com). Use `gunicorn run:app` as the start command.
- **Electron**: Use `electron-builder` (pre-configured) to package the app into a `.exe` installer.

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

## 🤝 Contact

Project Link: [https://github.com/your-username/yabatech-jss-management](https://github.com/your-username/yabatech-jss-management)
