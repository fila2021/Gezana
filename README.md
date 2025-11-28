# Gezana – Habesha Restaurant Booking System  
*A full-stack Django project for restaurant bookings, menu display, cancellations, and customer interaction.*

---

## 1. Overview

Gezana is a full-stack Django web application for a Habesha (Ethiopian & Eritrean) restaurant based in Dublin.  
It provides:

- Online table booking  
- Automatic table assignment  
- Double-booking prevention  
- Booking cancellation with a reference code  
- Menu display with categories  
- About & Contact information  
- Admin management system  

This project was developed for the Code Institute Full Stack Software Development Diploma (Milestone Project 3).

---

## 2. Project Goals

### External User Goals
- Browse the restaurant’s menu  
- Book a table quickly and easily  
- Receive confirmation and a unique cancellation code  
- Cancel bookings using their reference code  
- Learn more about Gezana and how to contact us  

### Site Owner Goals
- Receive accurate booking information  
- Prevent double bookings for the same table/time  
- Manage menu items without editing code  
- Allow customers to reach the restaurant easily  
- Organize tables, menu items, and bookings via Django admin  

---

## 3. Features

### ✔ Homepage
- Clean introduction  
- Navigation to Menu, Book, Cancel, About, Contact  

### ✔ Menu Page
- Menu items displayed by category  
- Individual dish detail page  
- Vegetarian flag  
- All items editable via Django admin  

### ✔ Booking System
- Name, email, phone, guests, date, time  
- Prevents past date bookings  
- Ensures valid opening hours  
- Allocates appropriate table automatically  
- Avoids double bookings  
- Shows success message  
- Generates unique booking reference code  

### ✔ Cancellation System
- Enter reference code to cancel booking  
- Booking removed from database  
- Error message for invalid code  

### ✔ About Page
- Restaurant story  
- Cultural background  
- Mission  

### ✔ Contact Page
- Location, email, phone  
- Opening times  

### ✔ Admin Area
- Add/edit/delete menu items  
- Create tables and set capacities  
- View and manage bookings  
- Filters, search, ordering  

---

## 4. Technologies Used

### Languages
- Python  
- HTML  
- CSS  

### Frameworks & Libraries
- Django  
- Django Messages Framework  

### Tools
- Git & GitHub  
- VS Code  
- Render (deployment)  

---

## 5. User Stories

### As a user:
- I want to view the menu to see what dishes are available.  
- I want to book a table for a specific date/time.  
- I want to receive confirmation that my booking is successful.  
- I want to cancel my booking if my plans change.  
- I want to see clear feedback if a booking fails.  
- I want to read about the restaurant.  
- I want to find contact information.  

### As a site owner:
- I want to manage menu items easily.  
- I want to avoid double bookings.  
- I want customers to book online without calling.  
- I want users to cancel their own bookings.  
- I want access to all booking data in admin.  

---

## 6. Database Schema

### Table Model
| Field         | Type        |
|---------------|-------------|
| table_number  | CharField   |
| capacity      | Integer     |

### MenuItem Model
| Field         | Type          |
|---------------|---------------|
| name          | CharField     |
| description   | TextField     |
| price         | DecimalField  |
| category      | ChoiceField   |
| is_vegetarian | BooleanField  |

### Booking Model
| Field     | Type          |
|-----------|---------------|
| name      | CharField     |
| email     | EmailField    |
| phone     | CharField     |
| guests    | Integer       |
| date      | DateField     |
| time      | TimeField     |
| table     | ForeignKey    |
| reference | CharField     |

---

## 7. Testing

### Manual Testing Summary

| Feature          | Test Performed                               | Result |
|------------------|-----------------------------------------------|--------|
| Booking          | Prevent past date                            | Pass   |
| Booking          | Prevent double booking                       | Pass   |
| Booking          | Valid bookings show success message          | Pass   |
| Cancellation     | Valid reference cancels booking              | Pass   |
| Cancellation     | Invalid reference shows error                | Pass   |
| Navigation       | All links route correctly                    | Pass   |
| Templates        | All extend base.html correctly               | Pass   |
| Form Validation  | Guests/date/time validated                   | Pass   |

### Validators
- HTML — W3C validator  
- CSS — Jigsaw validator  
- Python — PEP8 compliant  

---

## 8. Deployment (Render)

### Steps:
1. Push project to GitHub  
2. Create a *Web Service* on Render  
3. Connect GitHub repository  
4. Build command:

pip install -r requirements.txt
5. Start command:

gunicorn gezana.wsgi
6. Add environment variables:
- `SECRET_KEY`  
- `DEBUG=False`  
7. Run migrations:

python3 manage.py migrate
8. Collect static files:

python3 manage.py collectstatic
App will deploy and become live.
---
## 9. Running Locally
Clone the repo:
git clone https://github.com/fila2021/Gezana.git
cd Gezana
Create virtual environment:
python3 -m venv venv
source venv/bin/activate
Install dependencies:
pip install -r requirements.txt
Run migrations:
python3 manage.py migrate
Start server:
python3 manage.py runserver
Visit:
http://127.0.0.1:8000/

---

## 10. Credits

- Code Institute  
- Django Documentation  
- All content and development by the project author  

---

# ✨ Thank You For Visiting Gezana!

Proudly sharing Habesha culture through food and technology.











