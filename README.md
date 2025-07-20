# Mosque Facility Booking System

A web-based system for managing mosque facility bookings. Built as a final-year Diploma project for CSC2764 (Project Design, Implementation & Evaluation).

## Features

- User registration & login
- Check facility availability
- Make & manage bookings
- Upload payment receipts
- Admin dashboard (approve/reject bookings)
- Email notifications
- Booking report generation
- Profile & password management

## Tech Stack

- Python (Django)
- SQLite
- HTML/CSS

---

## ⚙️ How to Run the Project Locally

### Prerequisites
- Python 3.x
- pip
- virtualenv (recommended)

---

### 🔧 Setup Instructions

#### 1. Clone the Repository

git clone https://github.com/luqmnnnn/Mosque-Facility-Booking-System.git
cd Mosque-Facility-Booking-System
2. Create & Activate Virtual Environment (Optional but Recommended)
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
3. Install Dependencies
pip install -r requirements.txt

4. Run Database Migrations
python manage.py makemigrations
python manage.py migrate

6. Create Superuser (for Admin Access)
python manage.py createsuperuser

8. Start the Development Server
python manage.py runserver
Then open in your browser:
http://127.0.0.1:8000/

👤 Developer
Muhammad Luqman Aziz
Diploma in Computer Science
Kolej Profesional MARA Beranang
Session 1 2025/2026
