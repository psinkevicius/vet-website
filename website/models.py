import uuid
from datetime import timedelta, datetime
from sqlalchemy import Text
from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func


service_employees = db.Table(
    'service_employees',
    db.Column('service_id', db.Integer, db.ForeignKey('service.id', ondelete="CASCADE"), primary_key=True),
    db.Column('employee_id', db.Integer, db.ForeignKey('user.id', ondelete="CASCADE"), primary_key=True)
)


class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.String(10000))
    date = db.Column(db.DateTime(timezone=True), default=func.now())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    tags = db.Column(db.String(255), nullable=True)
    pinned = db.Column(db.Boolean, default=False)


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(150), nullable=False)
    last_name = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(20), default='customer')

    google_id = db.Column(db.String(255), unique=True, nullable=True)  # Unique Google ID
    google_picture = db.Column(db.String(255), nullable=True)  # Profile picture URL

    reset_token = db.Column(db.String(100), unique=True, nullable=True)
    reset_token_expiration = db.Column(db.DateTime, nullable=True)

    notes = db.relationship('Note', backref='user', lazy=True)

    employee_appointments = db.relationship(
        'Uzsakymas', foreign_keys='Uzsakymas.user_id', backref='assigned_employee', lazy=True
    )
    customer_appointments = db.relationship(
        'Uzsakymas', foreign_keys='Uzsakymas.uzsakovo_id', backref='customer', lazy=True
    )
    services = db.relationship(
        'Service',
        secondary=service_employees,
        backref=db.backref('assigned_employees', lazy='dynamic')  # Unique backref name
    )

    def generate_reset_token(self):
        self.reset_token = str(uuid.uuid4())
        self.reset_token_expiration = datetime.utcnow() + timedelta(hours=1)
        db.session.commit()

    def clear_reset_token(self):
        self.reset_token = None
        self.reset_token_expiration = None
        db.session.commit()


class Uzsakymas(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), nullable=False)
    tel_nr = db.Column(db.BigInteger, nullable=False)
    first_name = db.Column(db.String(150), nullable=False)
    last_name = db.Column(db.String(150), nullable=False)
    data = db.Column(db.String(10000), nullable=False)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Time, nullable=False)
    status = db.Column(db.String(50), default="Pending")
    uzsakovo_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete="CASCADE"))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete="CASCADE"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    service_id = db.Column(db.Integer, db.ForeignKey('service.id', ondelete="CASCADE"), nullable=False)
    animal_id = db.Column(db.Integer, db.ForeignKey('animal.id', ondelete="CASCADE"), nullable=False)
    treatment = db.Column(Text, nullable=True)

    species = db.Column(db.String(150), nullable=False)  # Species of the animal
    animal_name = db.Column(db.String(150), nullable=False)  # Name of the animal
    symptoms = db.Column(db.Text, nullable=True)  # Description of symptoms

    service = db.relationship('Service', backref='orders')
    employee = db.relationship('User', foreign_keys=[user_id])
    uzsakovas = db.relationship('User', foreign_keys=[uzsakovo_id])
    animal = db.relationship('Animal', back_populates='appointments')

    __table_args__ = (
        db.UniqueConstraint('user_id', 'date', 'time', name='unique_booking_per_employee'),
    )


class Service(db.Model):
    __tablename__ = 'service'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, nullable=False)
    duration = db.Column(db.Integer, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id', ondelete="CASCADE"), nullable=False)

    employees = db.relationship(
        'User',
        secondary=service_employees,
        backref=db.backref('services_assigned', lazy='dynamic')
    )


class Category(db.Model):
    __tablename__ = 'category'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False, unique=True)

    services = db.relationship('Service', backref='category', lazy=True)


class Animal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    species = db.Column(db.String(150), nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)  # Relationship with User
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())  # Timestamp

    # Relationships
    owner = db.relationship('User', backref=db.backref('animals', cascade="all, delete-orphan"))  # Each user can own multiple animals
    appointments = db.relationship('Uzsakymas', back_populates='animal', cascade="all, delete-orphan", lazy=True)


class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete="SET NULL"), nullable=True)  # Allow NULL author
    comment = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # Rating out of 5 stars
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)

    author = db.relationship('User', backref='feedbacks')  # Relationship with User table

