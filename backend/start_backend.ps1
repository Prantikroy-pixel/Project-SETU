# SETU Backend Startup Script
# Usage: .\start_backend.ps1
# Runs migrations and starts the Django dev server on port 8000

Write-Host "[SETU] Activating environment and checking dependencies..." -ForegroundColor Cyan

# Install requirements if needed
pip install -r requirements.txt -q

Write-Host "[SETU] Running database migrations..." -ForegroundColor Cyan
python manage.py migrate --run-syncdb 2>&1

Write-Host "[SETU] Starting Django development server on http://localhost:8000" -ForegroundColor Green
Write-Host "[SETU] API documentation: http://localhost:8000/api/" -ForegroundColor Green
Write-Host "[SETU] Admin panel: http://localhost:8000/admin/" -ForegroundColor Green
Write-Host ""

python manage.py runserver 0.0.0.0:8000
