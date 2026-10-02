# BILLPRO — Advanced Billing Management System

A polished, responsive billing web application built with **Python Flask, SQLite, HTML, advanced CSS and JavaScript**.

## Features
- Modern admin dashboard with 7-day revenue analytics
- POS-style invoice builder with live product search
- Customer management
- Product and inventory management with low-stock indicators
- Invoice history and searchable transactions
- Printable / PDF invoices
- Cash, UPI and Card payment selection
- Responsive desktop/tablet/mobile UI
- Light / dark theme with saved preference
- Secure password hashing for the demo account
- Environment-based Flask secret key
- Foreign-key database integrity and safer invoice creation

## Run on Windows
```bat
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
set BILLPRO_SECRET_KEY=replace-this-with-a-random-secret
python run.py
```

Open **http://127.0.0.1:5000**.

### Demo login
- Username: `admin`
- Password: `admin123`

The first startup creates `app/database/billing.db` automatically with demo products and customers.

## Project structure
```text
BILLPRO_Advanced_Billing_System/
├── app/
│   ├── database/db.py
│   ├── static/
│   │   ├── css/style.css
│   │   └── js/
│   │       ├── app.js
│   │       └── billing.js
│   ├── templates/
│   ├── __init__.py
│   └── routes.py
├── requirements.txt
├── run.py
└── README.md
```

## Production notes
Before public deployment, use a strong `BILLPRO_SECRET_KEY`, HTTPS, a production WSGI server, database backups, CSRF protection, role-based permissions and PostgreSQL/MySQL if the application grows beyond a small/local deployment.
