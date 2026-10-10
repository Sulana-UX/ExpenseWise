# Setup & Execution Guide

## 1. Prerequisites
- **Python 3.12+** installed and added to PATH.
- **Flutter 3.41+ & Dart 3.11+** installed.
- **Git** installed.

---

## 2. Backend Setup & Run

### Step 1: Create and Activate Virtual Environment
```powershell
# From the project root d:\ExpenseWise
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### Step 2: Install Dependencies
```powershell
pip install -r requirements.txt
```

### Step 3: Configure Environment
Copy `.env.example` from the root directory to `backend/.env` (or project root):
```powershell
cp ..\.env.example .env
```

### Step 4: Run the Backend Server
```powershell
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
Interactive API documentation is immediately available at:
👉 **http://127.0.0.1:8000/docs**

### Step 5: Run Backend Automated Tests
```powershell
pytest -v
```

---

## 3. Flutter Mobile Setup & Run

### Step 1: Install Flutter Packages
```powershell
cd mobile
flutter pub get
```

### Step 2: Run the Application

#### Option A: Run on Web (Instant Preview in Chrome)
```powershell
flutter run -d chrome
```

#### Option B: Run on Android Emulator / Physical Device
```powershell
flutter run -d android
```
*(Note: Inside the Android Emulator, use `http://10.0.2.2:8000` as the API Base URL to communicate with the host machine's backend).*

#### Option C: Run on Windows Desktop
```powershell
flutter run -d windows
```

### Step 3: Run Flutter Automated Tests
```powershell
flutter test
```
