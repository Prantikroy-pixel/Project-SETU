# SETU — Emergency Relief & Geospatial Logistics Platform

> **SETU** is an AI-powered disaster relief logistics and accessibility platform for real-time route monitoring, disruption prediction, demand-supply matching, GPS vehicle fleet tracking, and offline field reporting across Northeast India.

---

## 🌐 Live Production Links

* **Live Web Application**: [https://setu-jade-three.vercel.app](https://setu-jade-three.vercel.app)
* **GitHub Repository**: [https://github.com/abijitdas12/SETU.git](https://github.com/abijitdas12/SETU.git)
* **Vercel Inspection Dashboard**: [https://vercel.com/setu12/setu/NsAVCx21nE8Pysvp5pF64T1AQxPo](https://vercel.com/setu12/setu/NsAVCx21nE8Pysvp5pF64T1AQxPo)

---

## 📚 Complete Project Documentation

- 📄 **[System Architecture & Overview (`SYSTEM_INFO.md`)](file:///d:/SETU/SETU/SYSTEM_INFO.md)**: Full architecture breakdown, tech stack, AI risk model, database spatial compatibility layer, and Vercel serverless cloud setup.
- 📋 **[Project Changelog (`CHANGELOG.md`)](file:///d:/SETU/SETU/CHANGELOG.md)**: Detailed log of features, test suite runs, security remediation audits, and release updates.
- 🔌 **[REST API Reference (`docs/API_DOCUMENTATION.md`)](file:///d:/SETU/SETU/docs/API_DOCUMENTATION.md)**: DRF endpoints specification for authentication, needs, stockpiles, vehicles, and hazard predictions.

---

## 🚀 Quick Setup & Local Development

### 1. Backend Setup (Django & Python)
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

### 2. Frontend Setup (React & Vite)
```bash
cd frontend
npm install
npm run dev
```

### 3. Running Automated Tests
```bash
# Django REST Framework Unit Tests (23 tests)
python backend/manage.py test accounts core dashboard logistics matching

# AI Risk Model Engine Tests (14 tests)
python -m unittest discover matching_engine/tests/
```
