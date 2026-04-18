# Faculty Performance AI System

## Overview
The Faculty Performance AI System is a modern, modular, role-based dashboard engineered to comprehensively track, verify, and intuitively explore faculty performance metrics across multiple departments.

Built entirely on local state and powered by the Groq API (Whisper Transcription & Llama-3.1), the system offers administrators an integrated command center for academic benchmarking and provides faculty members with a seamless, AI-assisted interface—featuring a fully interactive, full-page voice orb.

## Core Features
- **Dynamic KPI Generation:** Algorithmically benchmarks precisely 11 faculty members across 9 completely populated departments (`CSE`, `ECE`, `ME`, `CIVIL`, `EEE`, `IT`, `AIDS`, `CSBS`, `BME`) adhering to strict distribution quotas (High Performers, Average, and Needs Improvement).
- **Intelligent Voice Mode:** An immersive, floating AI orb that you can speak to infinitely. Audio inputs are sent instantly for serverless processing and discarded—ensuring your privacy without clogging physical disk storage with `.wav` files. 
- **Evidence Verification Portal:** Faculty members can upload certificates securely against their KPIs, which are then passed meticulously to the LLM backend for rigorous AI authenticity review.
- **Glassmorphic Theming:** Built via Streamlit with a highly polished visual aesthetic featuring CSS glassmorphism, animated backgrounds, and customized dark-themed contrasts.

## Recent Updates
- **Strict Performance Quotas:** Mathematically finalized the dynamic probability distribution engine to strictly yield 11 profiles per department complying exactly with: 2 instances > 90%, 4 instances > 76%, 3 instances > 45%, and the bottom 2 < 45%.
- **Unified Full-Scope KPI Views:** Expanded the HOD and Principal dashboard tabs. All 17 granular KPI data points (Including NPTEL, workshops, industrial training, etc.) are now seamlessly visible without data truncation across every role's table.
- **Automated Port Handling:** `run_on_edge.bat` now intelligently detects and cleans up ghosted Streamlit background processes locked on Port 8505 prior to launching.

## How to Initialize & Run 

### 1. Database Initialization
Before the first run, or anytime you want to restore the data back to its original mathematical distribution, run the initializer script. This generates a fresh `faculty.db` with exactly 99 faculty members mapping to the unified login password (`1234`).
```powershell
.\venv\Scripts\python.exe database\init_database.py
```

### 2. Launch the Application
Simply trigger the automated batch file. This will spark the Streamlit background process and natively boot up your Microsoft Edge app attached to the dashboard.
```powershell
.\run_on_edge.bat
```

> **Note:** If you get a `Port 8505 is not available` error, it means an older script instance is locked in the background. Kill it quickly via PowerShell using:  
> `Stop-Process -Id (Get-NetTCPConnection -LocalPort 8505).OwningProcess -Force`

## Tech Stack
- Frontend Interface Layer: Streamlit
- Database Protocol: SQLite / SQLAlchemy
- Data Manipulation: Pandas
- AI Inference: Groq API (Whisper-large-v3-turbo / Llama-3.1)
