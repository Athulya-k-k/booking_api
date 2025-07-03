# 🏋️‍♀️ Fitness Studio Booking System 

A full-featured web application built with Django that allows users to view fitness classes, book or cancel slots, and manage bookings via a user-friendly dashboard. It also includes REST APIs for integration and automation.

---

## 🚀 Features

- User authentication (signup/login/logout)
- View upcoming fitness classes (Yoga, Zumba, HIIT)
- Book or cancel slots
- Class availability and countdown timer
- Role-based dashboards (Admin & User)
- RESTful API (View classes, Book classes, List user bookings)
- AJAX-based booking with loading feedback

---

## 🛠️ Tech Stack

- Python 3.8+
- Django 4+
- Django Rest Framework (DRF)
- SQLite3 or MySQL
- Bootstrap 5

---

## ⚙️ Setup Instructions

### 1. Clone the Repo
https://github.com/Athulya-k-k/booking_api.git

cd fitness-booking

# Create Virtual Environment

python -m venv env

env\Scripts\activate

# Run Migrations
python manage.py makemigrations
python managge.py migrate

# Create Superuser (for Admin Access)
python manage.py createsuperuser


# Run the Server

python manage.py runserver


Sample Credentials
Role	Username	Password
Admin	admin	    admin123
user	athulya	    anjushakk



API Endpoints (with DRF)
All APIs require authentication using DRF’s Session or Token Auth.

Method	Endpoint	       Description
GET 	/api/classes/	   List upcoming fitness classes
POST	/api/book/      	Book a class (needs class_id)
GET 	/api/my-bookings/	View logged-in user's bookings




