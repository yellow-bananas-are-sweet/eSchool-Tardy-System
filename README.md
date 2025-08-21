# eSchool Tardy System

A teacher-operated attendance system for **Cypress Woods High School** that connects directly to **eSchoolData (eSD)** to record tardies in real time.  
The system allows teachers to scan student IDs, look up student records, and automatically log tardy events into eSD via its API.

---

## Project Overview
This project consists of:
- **Frontend (Ionic React)** – A teacher interface for scanning student IDs and recording tardies.
- **Direct eSD API Integration** – Fetches student data and submits tardy attendance records directly from the frontend.

---

## Project Structure

```
eSchool-Tardy-System/
│
├── frontend/ → Ionic React project (teacher interface)
└── docs/ → Documentation and reference material
```

---

## Setup Instructions

### 1. Clone Repository
```bash
git clone https://github.com/yellow-bananas-are-sweet/eSchool-Tardy-System.git
cd eSchool-Tardy-System
```

### Frontend (Ionic React)
```bash
cd frontend
npm install
npm install -g @ionic/cli   # install Ionic CLI globally (only once per machine)
```



---

## Running the Project

### Start the Frontend
```bash
cd frontend
ionic serve
```

This launches the teacher interface at `http://localhost:8100`.



---

## eSD API Integration

We use eSchoolData API endpoints for:

- **Authentication** (`/oauth/token`)
- **Student Lookup** (`/ims/oneroster/v1p1/students/{id}`)
- **Attendance Reasons** (`/v1/attendanceReasons`)
- **Post Tardy Records** (`/v1/dailyAttendance` or `/v1/periodAttendance`)

**Full eSD API documentation:**
[API Reference – Renaissance/eSD](https://support.renaissance.com/s/article/API-Endpoints-with-Associated-Resource-Action-1752692902048?language=en_US)

eSchool Archietecture + more api info: https://guru.eschooldata.com/api/Developers/Docs

---

## Documentation

- **System Design** → `docs/system-overview.md`
- **API Flow** → `docs/api-flow.md` (login, lookup, attendance post)
- **Deployment Guide** → `docs/deployment.md`

---

## Current Plan

1. Set up teacher interface (Ionic React frontend).
2. Authenticate with eSD API.
3. Scan student ID → fetch student record.
4. Determine current period from bell schedule.
5. Post tardy record (daily or period attendance).
6. Store backup of all tardy logs in a local sheet/database for redundancy.

## Brands of integrations
 - Scanner: Zebra Symbol
 - Printer: Dymo label writer 490 turbo

 ## Data
 - ON PASS
  - Period
  - Grade Level
  - Current Time
 - Send data to Google Sheet