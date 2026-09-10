# Event & Ticket Booking System

A deliberately small Flask/MySQL application for event browsing and ticket booking. It has a vanilla HTML/CSS/JavaScript frontend and a REST API. There are no Docker, cloud, or deployment files, so you can add those as learning exercises later.

## Features

- User registration, login, JWT authentication, and hashed passwords
- Public event search and event/ticket details
- Authenticated bookings, cancellation, and personal booking history
- Admin-only event creation/editing/cancellation and ticket-type management
- MySQL transactions plus `SELECT ... FOR UPDATE` row locks when allocating or returning tickets
- `GET /health` returns `{"status":"healthy"}`

## Structure

- `backend/app/` contains the Flask application, relational models, authorization helper, and API routes.
- `backend/tests/` contains basic API tests.
- `frontend/` contains static pages, CSS, and browser JavaScript. The frontend expects Flask at `http://localhost:5000`.

## Database schema

SQLAlchemy creates the requested relational tables: `users`, `events`, `ticket_types`, `bookings`, and `booking_items`. Foreign keys connect events to ticket types, bookings to users/events, and booking items to bookings/ticket types.

## Local setup

1. Create a MySQL database: `CREATE DATABASE ticket_booking;`
2. Copy `.env.example` to `.env` and set your MySQL values and a strong `JWT_SECRET`.
3. Create and activate a Python virtual environment, then install dependencies:

   `pip install -r backend/requirements.txt`

4. Create the tables once from the project root:

   `cd backend`

   `flask --app run.py shell`

   Then run `from app.models import db; db.create_all()`.
5. Start the API: `python run.py`
6. Open `frontend/index.html` in a browser (or serve the `frontend` folder with any simple static file server).

To create an administrator, change that user's `role` column from `user` to `admin` in MySQL. This is intentionally explicit rather than exposing public admin registration.

## API

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/auth/register`, `/api/auth/login` | Account access |
| GET/POST | `/api/events` | Browse/create (admin) events |
| GET/PUT/DELETE | `/api/events/<id>` | Event detail/manage (admin writes) |
| GET/POST | `/api/events/<id>/tickets` | Ticket list/create (admin write) |
| PUT | `/api/events/<id>/tickets/<ticket_id>` | Edit ticket type (admin) |
| POST/GET | `/api/bookings` | Create/list bookings |
| GET | `/api/bookings/<id>` | Booking detail |
| POST | `/api/bookings/<id>/cancel` | Cancel and restore tickets |

Supply JWTs as `Authorization: Bearer <token>` for protected routes.

## Tests

From `backend`, run `pytest`. Tests use an in-memory SQLite database; production booking locks take effect when using MySQL/InnoDB.
