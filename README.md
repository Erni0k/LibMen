[![Python 3.14+](https://img.shields.io/badge/python-3.14%2B-blue.svg)](https://www.python.org/downloads/)
[![Django 6.0.3](https://img.shields.io/badge/django-6.0.3-darkgreen.svg)](https://www.djangoproject.com/)
[![PostgreSQL 15+](https://img.shields.io/badge/postgresql-15%2B-336791.svg)](https://www.postgresql.org/)
[![License MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

# LibMen - Library Management System

Django-based library rental system with role-based access control, book inventory management, and fine tracking.

## Quick Start

### Requirements
- Python 3.14+, PostgreSQL 15+, pip

### Setup
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure .env (see .env.example)
DEBUG=True
SECRET_KEY=your-secret-key
DATABASE_NAME=biblioteka_db
DATABASE_USER=biblioteka_user
DATABASE_PASSWORD=your_password

# 3. Setup database
python manage.py migrate

# 4. Load demo data
python manage.py populate_db

# 5. Run server
python manage.py runserver
```

Visit: `http://127.0.0.1:8000/`

## Demo Accounts

| Username | Password | Role |
|----------|----------|------|
| admin | admin123 | Admin |
| maria_staff | password123 | Staff |
| ola_kowalczyk | password123 | User |
| jan_kowalski | password123 | User |

11 additional demo users available with password `password123`.

## Technology Stack

- **Backend**: Django 6.0.3, Python 3.14
- **Database**: PostgreSQL 15+
- **Frontend**: Bootstrap 5.1.3, Jinja2
- **Authentication**: Django built-in + custom User model with roles

## Key Features

### User
- Browse/search books with filtering
- Borrow, return, reserve books
- Track loans and fines
- Pay fines online

### Staff
- Dashboard with statistics
- Manage loans, reservations, fines
- Add/remove books and copies
- Track user activity

### Admin
- User management (roles, deletion, password reset)
- User statistics and monitoring

### System
- Custom 404/403 error pages
- Role-based access control
- Fine calculation (2 PLN/day overdue)
- Real-time book availability tracking

## Database Models

- **User** (roles: admin/staff/user)
- **Book, BookCopy, Author, Category**
- **Loan** (rental transactions)
- **Reservation** (with 7-day expiration)
- **Fine** (overdue penalties with payment tracking)

## Project Structure

```
libmen/
├── config/              # Django settings & URLs
├── library/
│   ├── models.py       # 8 core models
│   ├── views.py        # 25+ views (545 lines)
│   ├── urls.py         # Route definitions
│   ├── middleware.py   # Error handling
│   ├── management/
│   │   └── populate_db.py  # Demo data seeder
│   └── templates/      # HTML templates (14 files)
├── manage.py
└── requirements.txt
```

## Main Routes

**Public**: `/`, `/book/<id>/`, `/register/`, `/login/`

**User**: `/my-rentals/`, `/my-reservations/`, `/my-fines/`, `/borrow/`, `/return/`, `/reserve/`, `/pay-fine/`

**Staff**: `/staff/`, `/staff/loans/`, `/staff/fines/`, `/staff/manage-books/`

**Admin**: `/staff/admin/users/`

**Error**: `/test-404/`, `/test-403/` (dev mode)

## License

MIT
