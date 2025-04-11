from flask import Blueprint
from .models import User, Service
import re
from . import mail
from flask_mail import Message


utils = Blueprint('utils', __name__)


def get_user_by_id(user_id):
    user = User.query.filter_by(id=user_id).first()
    return user


def is_valid_email(email):

    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

    if re.match(email_pattern, email):
        return True
    else:
        return False


def is_strong_password(password):

    if len(password) < 8:
        return False

    if not any(char.isupper() for char in password):
        return False

    if not any(char.islower() for char in password):
        return False

    if not any(char.isdigit() for char in password):
        return False

    if not any(char in "!@#$%^&*()-_=+[{]}|;:'\",<.>/?`~" for char in password):
        return False

    return True


def send_status_update_email(customer, employee, appointment, service, new_status):
    """Send email notifications when appointment status is updated."""

    # Email to the Customer
    customer_msg = Message(
        subject=f"Paskyrimo būsenos atnaujinimas: {new_status}",
        sender="kenkikenkitor@gmail.com",  # Replace with your email
        recipients=[customer.email]
    )
    customer_msg.body = f"""
    Gerb. {customer.first_name},

    Jūsų susitikimo būsena buvo atnaujinta. Štai išsami informacija:

    Paslauga: {service.name}
    Data ir laikas: {appointment.date} {appointment.time}
    Gydytojas: {employee.first_name} {employee.last_name}
    Statusas: {new_status}

    
    Dėkojame, kad pasirinkote mūsų paslaugą.
    """

    # Email to the Employee
    employee_msg = Message(
        subject=f"Paskyrimo būsena atnaujinta: {new_status}",
        sender="kenkikenkitor@gmail.com",  # Replace with your email
        recipients=[employee.email]
    )
    employee_msg.body = f"""
    Sveiki {employee.first_name},

    Jūsų vadovaujamo susitikimo būsena buvo atnaujinta. Štai išsami informacija:

    Paslauga: {service.name}
    Data ir laikas: {appointment.date} {appointment.time}
    Klientas: {appointment.first_name} {appointment.last_name} 
           (El. paštas: {appointment.email}, Tel. nr.: {appointment.tel_nr})
    Statusas: {new_status}

    Atkreipkite dėmesį į atnaujintą būseną.

    Ačiū!
    """

    # Send emails
    with mail.connect() as conn:
        conn.send(customer_msg)
        conn.send(employee_msg)


def send_email_notifications(customer_email, customer_name, employee, appointment):
    """Send email notifications to both the customer and the employee."""
    # Ensure service is fetched properly
    service = Service.query.get(appointment.service_id)
    if not service:
        raise ValueError("Nepavyko rasti paslaugos, susijusios su susitikimu.")

    # Email to the Customer
    customer_msg = Message(
        subject="Apsilankymo informacija",
        sender="kenkikenkitor@gmail.com",  # Replace with your email
        recipients=[customer_email]
    )
    customer_msg.body = f"""
    Gerb. {customer_name},

    Jūsų paskyrimas sėkmingai patvirtintas. Štai išsami informacija:

    Paslauga: {service.name}
    Data ir laikas: {appointment.date} {appointment.time}
    Gydytojas: {employee.first_name} {employee.last_name}
    Augintinis: {appointment.animal_name} ({appointment.species})
    Simptomai: {appointment.symptoms or 'N/A'}

    Dėkojame, kad pasirinkote mus!

    """

    # Email to the Employee
    employee_msg = Message(
        subject="Pranešimas apie naują apsilankymą",
        sender="kenkikenkitor@gmail.com",  # Replace with your email
        recipients=[employee.email]
    )
    employee_msg.body = f"""
    Sveiki {employee.first_name},

    Patvirtintas naujas susitikimas. Štai išsami informacija:

    Paslauga: {service.name}
    Data ir laikas: {appointment.date} {appointment.time}
    Klientas: {customer_name} ({customer_email}, {appointment.tel_nr})
    Augintinis: {appointment.animal_name} ({appointment.species})
    Simptomai: {appointment.symptoms or 'N/A'}

    Prašome atitinkamai pasiruošti.

    Ačiū!
    """

    # Send the emails
    with mail.connect() as conn:
        conn.send(customer_msg)
        conn.send(employee_msg)

