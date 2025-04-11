from flask import Blueprint, render_template, request, flash, jsonify, url_for
from flask import abort
from . import db
from .models import User, Uzsakymas, Service, Category, Animal
from flask_login import login_required, current_user
from datetime import datetime, timedelta, date
from flask import session, redirect
from flask import current_app as app
from .utils import get_user_by_id, send_status_update_email, send_email_notifications

appointment = Blueprint('appointment', __name__, template_folder='templates/appointment_templates')


@appointment.route('/uzsakymai', methods=['GET'])
@login_required
def uzsakymai():
    page = request.args.get('page', 1, type=int)
    per_page = 2 if current_user.role != 'admin' else 10  # Admins can use this too
    search_query = request.args.get('search', '').strip()

    # Build the base query
    base_query = Uzsakymas.query
    if current_user.role == 'employee':
        base_query = base_query.filter_by(user_id=current_user.id)  # Employee-specific
    elif current_user.role == 'customer':
        base_query = base_query.filter_by(uzsakovo_id=current_user.id)  # Customer-specific
    elif current_user.role != 'admin':
        abort(403)  # Restrict access for other roles

    # Join related tables for search functionality
    base_query = base_query.join(Service, Uzsakymas.service).join(User, Uzsakymas.employee)

    # Apply search filters
    if search_query:
        base_query = base_query.filter(
            db.or_(
                Uzsakymas.animal_name.ilike(f"%{search_query}%"),
                Uzsakymas.species.ilike(f"%{search_query}%"),
                Service.name.ilike(f"%{search_query}%"),
                Uzsakymas.date.cast(db.String).ilike(f"%{search_query}%"),
                Uzsakymas.time.cast(db.String).ilike(f"%{search_query}%"),
                (User.first_name + " " + User.last_name).ilike(f"%{search_query}%")
            )
        )

    # Paginate results
    paginated_orders = base_query.paginate(page=page, per_page=per_page)

    return render_template(
        "uzsakymai.html",
        user=current_user,
        orders=paginated_orders.items,
        pagination=paginated_orders,
        search_query=search_query,
        get_user_by_id=get_user_by_id
    )


@appointment.route('/uzsakymai/update-treatment/<int:uzsakymas_id>', methods=['POST'])
@login_required
def update_treatment(uzsakymas_id):
    if current_user.role != 'employee':
        return jsonify({'error': 'Neturite prieigos'}), 403

    # Get the appointment
    uzsakymas = Uzsakymas.query.get(uzsakymas_id)
    if not uzsakymas:
        return jsonify({'error': 'Apsilankymas nerastas'}), 404

    # Get the treatment data from the request
    data = request.get_json()
    treatment = data.get('treatment')

    if treatment is None:
        return jsonify({'error': 'Gydymas reikalingas'}), 400

    # Update the treatment field
    uzsakymas.treatment = treatment
    db.session.commit()

    return jsonify({'message': 'Gydymas atnaujintas sėkmingai', 'treatment': treatment})


@appointment.route('/uzsakymai/update-datetime/<int:uzsakymas_id>', methods=['POST'])
@login_required
def update_datetime(uzsakymas_id):
    # Get the appointment
    uzsakymas = Uzsakymas.query.get(uzsakymas_id)

    # Check if the appointment exists
    if not uzsakymas:
        return jsonify({'error': 'Apsilankymas nerastas'}), 404

    # Check if the current user has permission (e.g., only employees or admins can edit)
    if current_user.role != 'employee':
        return jsonify({'error': 'Leidimas atmestas'}), 403

    # Parse the request data
    data = request.get_json()
    new_date = data.get('date')
    new_time = data.get('time')

    # Validate the inputs
    try:
        if new_date:
            uzsakymas.date = datetime.strptime(new_date, '%Y-%m-%d').date()
        if new_time:
            uzsakymas.time = datetime.strptime(new_time, '%H:%M').time()
    except ValueError:
        return jsonify({'error': 'Neteisingas datos arba laiko formatas'}), 400

    # Save changes to the database
    db.session.commit()

    return jsonify({'success': True, 'message': 'Data ir laikas sėkmingai atnaujinti.'})


@appointment.route('/uzsakymai/update-status/<int:uzsakymas_id>', methods=['POST'])
@login_required
def update_status(uzsakymas_id):
    # Fetch the appointment
    uzsakymas = Uzsakymas.query.get(uzsakymas_id)

    # Check if the appointment exists
    if not uzsakymas:
        return jsonify({'error': 'Apsilankymas nerastas'}), 404

    # Check if the user has permission
    if current_user.role != 'employee':
        return jsonify({'error': 'Leidimas atmestas'}), 403

    # Parse the new status from the request
    data = request.get_json()
    new_status = data.get('status')

    # Validate the status
    if new_status not in ['Vykdoma', 'Atlikta', 'Atšaukta']:
        return jsonify({'error': 'Netinkamas statusas'}), 400

    # Update the status
    uzsakymas.status = new_status
    db.session.commit()

    # Fetch related data
    customer = User.query.get(uzsakymas.uzsakovo_id)
    employee = User.query.get(uzsakymas.user_id)
    service = Service.query.get(uzsakymas.service_id)

    if not customer or not employee or not service:
        return jsonify({'error': 'Susiję duomenys nerasti'}), 404

    # Send email notifications
    try:
        send_status_update_email(customer, employee, uzsakymas, service, new_status)
    except Exception as e:
        app.logger.error(f"Nepavyko išsiųsti būsenos atnaujinimo el. laiškų: {e}")

    return jsonify({'success': True, 'message': 'Būsena atnaujinta ir pranešimai sėkmingai išsiųsti.'})


@appointment.route('/uzsakymai/select-service', methods=['GET', 'POST'])
@login_required
def select_service():
    # Check if the form is submitted specifically for a past date selection
    if request.form.get('past_date_selected'):
        flash('Negalima pasirinkti pastarųjų dienų.', 'error')
        return redirect(url_for('appointment.select_service'))

    if request.method == 'POST':
        service_id = request.form.get('service_id')
        employee_id = request.form.get('employee_id')
        date_str = request.form.get('date')  # Capture selected date

        # Validate input
        if not service_id or not employee_id or not date_str:
            flash('Pasirinkite kategoriją, paslaugą, darbuotoją ir datą.', 'error')
            return redirect(url_for('appointment.select_service'))

        # Convert the date from string to a date object to validate it
        try:
            selected_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            flash('Netinkamas datos formatas.', 'error')
            return redirect(url_for('appointment.select_service'))

        # Store the selected service, employee, and date in session data
        session['service_id'] = service_id
        session['employee_id'] = employee_id
        session['date'] = date_str  # Store date as string to keep it compatible for storage

        return redirect(url_for('appointment.select_time'))  # Redirect to the next step (time selection)

    # Fetch categories and employees
    categories = Category.query.all()  # Fetch all categories
    today_date = date.today().isoformat()  # Get today's date as a string (e.g., '2023-10-15')

    return render_template('select_service.html', user=current_user, categories=categories, today_date=today_date)


@appointment.route('/uzsakymai/get-services/<int:category_id>', methods=['GET'])
@login_required
def get_services(category_id):
    # Fetch services for the given category
    services = Service.query.filter_by(category_id=category_id).all()

    # Return services as JSON
    return jsonify({
        'services': [{'id': service.id, 'name': service.name} for service in services]
    })


@appointment.route('/uzsakymai/get-employees/<int:service_id>', methods=['GET'])
@login_required
def get_employees(service_id):
    # Fetch employees associated with the given service via the many-to-many relationship
    service = Service.query.get(service_id)

    if not service:
        return jsonify({'error': 'Paslauga nerasta'}), 404

    employees = service.employees  # Access the employees associated with this service

    # Return employees as JSON
    return jsonify({
        'employees': [{'id': employee.id, 'name': f"{employee.first_name}", 'last_name': f"{employee.last_name}"} for employee in employees]
    })


@appointment.route('/uzsakymai/delete/<int:uzsakymas_id>', methods=['POST'])
@login_required
def delete_uzsakymas(uzsakymas_id):
    uzsakymas = Uzsakymas.query.get(uzsakymas_id)

    # Log if the appointment is not found
    if not uzsakymas:
        app.logger.warning(f"Bandymas ištrinti neegzistuojančio susitikimo su id: {uzsakymas_id}")
        return jsonify({"error": "Apsilankymas nerastas"}), 404

    # Log successful deletion
    app.logger.info(f"Appointment with id {uzsakymas_id} deleted by user {current_user.email}")
    db.session.delete(uzsakymas)
    db.session.commit()

    return jsonify({"success": True})


@appointment.route('/uzsakymai/select-time', methods=['GET', 'POST'])
@login_required
def select_time():
    if request.method == 'POST':
        time_str = request.form.get('time')
        selected_date = session.get('date')
        employee_id = session.get('employee_id')
        service_id = session.get('service_id')

        if not time_str or not selected_date or not employee_id or not service_id:
            flash('Trūksta apsilankymo informacijos. Pasirinkite paslaugą, darbuotoją ir laiką.', 'error')
            return redirect(url_for('appointment.select_time'))

        # Convert selected time and calculate end time
        selected_time = datetime.strptime(time_str, '%H:%M').time()
        service = Service.query.get(service_id)
        if not service:
            flash('Paslauga nerasta. Pasirinkite tinkamą paslaugą.', 'error')
            return redirect(url_for('appointment.select_service'))

        service_duration = timedelta(minutes=service.duration)
        selected_start_datetime = datetime.combine(datetime.strptime(selected_date, "%Y-%m-%d"), selected_time)
        selected_end_datetime = selected_start_datetime + service_duration

        # Check for overlapping appointments
        existing_appointments = Uzsakymas.query.filter_by(
            user_id=employee_id,
            date=selected_date
        ).all()

        for appointment in existing_appointments:
            appointment_start_datetime = datetime.combine(appointment.date, appointment.time)
            appointment_service = Service.query.get(appointment.service_id)
            appointment_duration = timedelta(minutes=appointment_service.duration)
            appointment_end_datetime = appointment_start_datetime + appointment_duration

            # Check overlap
            if (selected_start_datetime < appointment_end_datetime and
                    selected_end_datetime > appointment_start_datetime):
                flash('Pasirinktas laikas šiam darbuotojui jau rezervuotas. Pasirinkite kitą laiką.', 'error')
                return redirect(url_for('appointment.select_time'))

        # Proceed with creating the booking
        session['time'] = time_str
        return redirect(url_for('appointment.enter_personal_info'))

    # Generate working hours based on the day
    employee_id = session.get('employee_id')
    selected_date = session.get('date')
    service_id = session.get('service_id')

    if not employee_id or not selected_date or not service_id:
        flash('Pirmiausia pasirinkite paslaugą, darbuotoją ir datą.', 'error')
        return redirect(url_for('appointment.select_service'))

    service = Service.query.get(service_id)
    if not service:
        flash('Paslauga nerasta. Pasirinkite tinkamą paslaugą.', 'error')
        return redirect(url_for('appointment.select_service'))

    service_duration = service.duration
    appointments = Uzsakymas.query.filter_by(user_id=employee_id, date=selected_date).all()

    # Determine working hours
    selected_date_obj = datetime.strptime(selected_date, "%Y-%m-%d").date()
    if selected_date_obj.weekday() == 5:  # Saturday
        start_time = datetime.strptime("10:00", "%H:%M")
        end_time = datetime.strptime("14:00", "%H:%M")
    else:
        start_time = datetime.strptime("09:00", "%H:%M")
        end_time = datetime.strptime("17:00", "%H:%M")

    # Generate available slots
    booked_intervals = []
    for appointment in appointments:
        appointment_start_time = appointment.time
        appointment_service = Service.query.get(appointment.service_id)
        appointment_duration = timedelta(minutes=appointment_service.duration)
        appointment_end_time = (datetime.combine(appointment.date, appointment_start_time) + appointment_duration).time()
        booked_intervals.append((appointment_start_time, appointment_end_time))

    all_time_slots = generate_time_intervals(start_time, end_time, service_duration)
    available_times = []

    for time_slot in all_time_slots:
        slot_start_time = datetime.strptime(time_slot, '%H:%M').time()
        slot_end_time = (datetime.combine(datetime.today(), slot_start_time) + timedelta(minutes=service_duration)).time()
        if not any(slot_start_time < end and slot_end_time > start for start, end in booked_intervals):
            available_times.append(time_slot)

    return render_template('select_time.html', user=current_user, available_times=available_times)


def generate_time_intervals(start_time, end_time, interval_minutes):
    """Generates time intervals based on start and end time and duration."""
    times = []
    current_time = start_time
    while current_time < end_time:
        times.append(current_time.strftime('%H:%M'))
        current_time += timedelta(minutes=interval_minutes)
    return times


@appointment.route('/uzsakymai/get-busy-dates/<int:employee_id>', methods=['GET'])
@login_required
def get_busy_dates(employee_id):
    # Fetch all appointments for the employee
    appointments = Uzsakymas.query.filter_by(user_id=employee_id).all()

    # Group appointments by date
    busy_dates = {}
    for appointment in appointments:
        date_str = appointment.date.strftime('%Y-%m-%d')
        if date_str not in busy_dates:
            busy_dates[date_str] = []
        appointment_start_time = appointment.time
        appointment_service = Service.query.get(appointment.service_id)
        appointment_duration = timedelta(minutes=appointment_service.duration)
        appointment_end_time = (datetime.combine(appointment.date, appointment_start_time) + appointment_duration).time()
        busy_dates[date_str].append((appointment_start_time, appointment_end_time))

    fully_booked_dates = []
    for date, intervals in busy_dates.items():
        date_obj = datetime.strptime(date, "%Y-%m-%d").date()

        # Set working hours dynamically
        if date_obj.weekday() == 5:  # Saturday
            start_time = datetime.strptime("10:00", "%H:%M")
            end_time = datetime.strptime("14:00", "%H:%M")
        else:
            start_time = datetime.strptime("09:00", "%H:%M")
            end_time = datetime.strptime("17:00", "%H:%M")

        # Generate intervals
        all_intervals = generate_time_intervals(start_time, end_time, 30)

        # Check if all intervals are booked
        all_booked = True
        for interval in all_intervals:
            interval_start = datetime.strptime(interval, '%H:%M').time()
            interval_end = (datetime.combine(datetime.today(), interval_start) + timedelta(minutes=30)).time()

            # If any interval is not booked, the day is not fully booked
            if not any(interval_start < end and interval_end > start for start, end in intervals):
                all_booked = False
                break

        if all_booked:
            fully_booked_dates.append(date)

    return jsonify({'busy_dates': fully_booked_dates, 'partially_busy_dates': []})


@appointment.route('/uzsakymai/get-available-times', methods=['POST'])
@login_required
def get_available_times():
    employee_id = request.json.get('employee_id')
    selected_date = request.json.get('date')
    service_id = request.json.get('service_id')

    if not employee_id or not selected_date or not service_id:
        return jsonify({'error': 'Neteisinga įvestis'}), 400

    # Get the service details
    service = Service.query.get(service_id)
    if not service:
        return jsonify({'error': 'Service not found'}), 404

    service_duration = service.duration

    # Fetch appointments for the selected employee and date
    appointments = Uzsakymas.query.filter_by(user_id=employee_id, date=selected_date).all()

    # Generate busy intervals
    busy_intervals = []
    for appointment in appointments:
        appointment_start_time = appointment.time
        appointment_service = Service.query.get(appointment.service_id)
        appointment_duration = timedelta(minutes=appointment_service.duration)
        appointment_end_time = (datetime.combine(appointment.date, appointment_start_time) + appointment_duration).time()

        busy_intervals.append((appointment_start_time, appointment_end_time))

    # Generate available slots
    start_time = datetime.strptime("09:00", "%H:%M")
    end_time = datetime.strptime("17:00", "%H:%M")
    all_time_slots = generate_time_intervals(start_time, end_time, service_duration)
    available_times = []

    for time_slot in all_time_slots:
        slot_start_time = datetime.strptime(time_slot, '%H:%M').time()
        slot_end_time = (datetime.combine(datetime.today(), slot_start_time) + timedelta(minutes=service_duration)).time()

        if not any(slot_start_time < end and slot_end_time > start for start, end in busy_intervals):
            available_times.append(time_slot)

    return jsonify({'available_times': available_times})


@appointment.route('/uzsakymai/personal-info', methods=['GET', 'POST'])
@login_required
def enter_personal_info():
    if request.method == 'POST':
        # Get data from form
        email = request.form.get('email')
        tel_nr = request.form.get('tel_nr')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        animal_id = request.form.get('animal_id')
        symptoms = request.form.get('symptoms')

        if animal_id == 'new':
            # For new animal, get species and name from form
            species = request.form.get('new_species')
            animal_name = request.form.get('new_animal_name')

            if not species or not animal_name:
                flash('Nurodykite naujo gyvūno rūšį ir pavadinimą.', 'error')
                return redirect(url_for('appointment.enter_personal_info'))
        else:
            # For existing animal, get details from hidden inputs
            species = request.form.get('species')
            animal_name = request.form.get('animal_name')

        # Validate required fields
        if not (email and tel_nr and first_name and last_name and species and animal_name):
            flash('Visi laukai, išskyrus "simptomai", yra privalomi.', 'error')
            return redirect(url_for('appointment.enter_personal_info'))

        # Store data in session
        session['email'] = email
        session['tel_nr'] = tel_nr
        session['first_name'] = first_name
        session['last_name'] = last_name
        session['species'] = species
        session['animal_name'] = animal_name
        session['symptoms'] = symptoms

        return redirect(url_for('appointment.confirm_appointment'))

    return render_template('personal_info.html', user=current_user)


@appointment.route('/uzsakymai/confirm', methods=['GET', 'POST'])
@login_required
def confirm_appointment():
    if request.method == 'POST':
        # Check if required session data is available
        required_fields = [
            'email', 'tel_nr', 'first_name', 'last_name', 'service_id',
            'date', 'time', 'employee_id', 'species', 'animal_name'
        ]  # 'symptoms' removed from required_fields
        missing_fields = [field for field in required_fields if not session.get(field)]

        if missing_fields:
            app.logger.warning(f"Paskyrimo patvirtinimo bandymas trūkstant seanso duomenų: {missing_fields}")
            flash('Trūksta kai kurios būtinos informacijos. Pradėkite rezervavimo procesą iš naujo.', 'error')
            return redirect(url_for('appointment.select_service'))

        # Check if the animal already exists for the current user
        animal = Animal.query.filter_by(
            name=session.get('animal_name'),
            species=session.get('species'),
            owner_id=current_user.id
        ).first()

        # If the animal doesn't exist, create a new one
        if not animal:
            animal = Animal(
                name=session.get('animal_name'),
                species=session.get('species'),
                owner_id=current_user.id
            )
            db.session.add(animal)
            db.session.commit()  # Commit to generate the ID for the new animal

        # Create a new appointment
        new_uzsakymas = Uzsakymas(
            email=session.get('email'),
            tel_nr=session.get('tel_nr'),
            first_name=session.get('first_name'),
            last_name=session.get('last_name'),
            data=session.get('service_id'),  # Reference to selected service
            date=datetime.strptime(session.get('date'), "%Y-%m-%d").date(),
            time=datetime.strptime(session.get('time'), "%H:%M").time(),
            user_id=session.get('employee_id'),  # Assigned employee
            uzsakovo_id=current_user.id,
            status="Vykdoma",
            service_id=session.get('service_id'),
            species=session.get('species'),
            animal_name=session.get('animal_name'),
            symptoms=session.get('symptoms') or "",  # Default to empty string if not provided
            animal_id=animal.id  # Link the appointment to the animal
        )

        db.session.add(new_uzsakymas)
        db.session.commit()

        # Log successful appointment creation
        app.logger.info(
            f"Naujas susitikimas sėkmingai sukurtas vartotojui: {current_user.email}, "
            f"service_id: {session.get('service_id')}, employee_id: {session.get('employee_id')}"
        )

        # Send email notifications
        try:
            send_email_notifications(
                customer_email=session.get('email'),
                customer_name=f"{session.get('first_name')} {session.get('last_name')}",
                employee=User.query.get(session.get('employee_id')),
                appointment=new_uzsakymas
            )
        except Exception as e:
            app.logger.error(f"Nepavyko išsiųsti pranešimų el. paštu: {str(e)}")
            flash('Paskyrimas patvirtintas, bet el. pašto pranešimų išsiųsti nepavyko.', 'error')

        # Clear session data after successful booking
        session.clear()
        flash('Jūsų susitikimas sėkmingai sudarytas!', 'success')
        return redirect(url_for('appointment.uzsakymai'))

    # Prepare data for the confirmation page
    service = Service.query.get(session.get('service_id'))
    employee = User.query.get(session.get('employee_id'))

    return render_template(
        'confirm_appointment.html', user=current_user, service=service, employee=employee, session=session
    )




