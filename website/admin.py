from flask import Blueprint, render_template, request, flash, jsonify, url_for
from flask import abort
from . import db, LOG_FILE
from .models import User, Uzsakymas, Service, Category, service_employees
from flask_login import login_required, current_user
from datetime import datetime
from flask import redirect
from flask import current_app as app
from werkzeug.security import generate_password_hash
from .utils import get_user_by_id

admin = Blueprint('admin', __name__, template_folder='templates/admin_templates')


@admin.route('/admin/apsilankymai_admin', methods=['GET'])
@login_required
def apsilankymai_admin():
    # Determine what appointments to show based on user role
    if current_user.role == 'admin':
        orders = Uzsakymas.query.all()
    else:
        abort(403)

    # Handle AJAX request for partial content
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render_template("apsilankymai_admin.html", user=current_user, orders=orders, get_user_by_id=get_user_by_id)

    # Otherwise, return full page or redirect
    return redirect('/admin')


@admin.route('/admin/naudotojai', methods=['GET', 'POST'])
@login_required
def naudotojai():
    # Ensure only admins can access this route
    if current_user.role != 'admin':
        app.logger.warning(f"Unauthorized access attempt to /naudotojai-page by user: {current_user.email}")
        abort(403)

    all_users = User.query.all()

    # Handle POST requests for updating users
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        user = User.query.get(user_id)

        if not user:
            app.logger.warning(f"User not found for update attempt with user_id: {user_id} by admin: {current_user.email}")
            flash('Naudotojas nerastas arba neturi leidimo atnaujinti informacijos.', category='error')
            return '', 204  # Return empty response for AJAX handling

        email = request.form.get('email')
        first_name = request.form.get('first_name')
        role = request.form.get('role')

        if not (email and first_name and role):
            app.logger.warning(f"Invalid data provided for user update: user_id={user_id}, email={email}, first_name={first_name}, role={role} by admin: {current_user.email}")
            flash('Netinkami naudotojo duomenys.', category='error')
            return '', 204  # Empty response for AJAX handling

        # Save updates
        user.email = email
        user.first_name = first_name
        user.role = role
        db.session.commit()

        app.logger.info(f"User information updated successfully by admin: {current_user.email}, updated user_id: {user_id}")
        flash('Naudotojas informacija sėkmingai atnaujinta!', category='success')

    # Render the partial template only
    return render_template("naudotojai.html", users=all_users)


@admin.route('/admin/naudotojai/add-user', methods=['POST'])
@login_required
def add_user():
    if current_user.role != 'admin':
        return jsonify({'error': 'Neleistina'}), 403

    data = request.get_json()
    email = data.get('email')
    first_name = data.get('first_name')
    last_name = data.get('last_name')
    password = data.get('password')  # Capture password input
    role = data.get('role', 'customer')  # Default to 'customer' if role is not provided

    # Validate required fields
    if not email or not first_name or not last_name or not password:
        return jsonify({'error': 'Visi laukai yra būtini'}), 400

    # Check if email already exists
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({'error': 'Naudotojas su šiuo el. pašto adresu jau egzistuoja'}), 400

    # Hash the password
    hashed_password = generate_password_hash(password)

    # Create the new user
    new_user = User(
        email=email,
        password=hashed_password,
        first_name=first_name,
        last_name=last_name,
        role=role
    )
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'success': True, 'user': {
        'id': new_user.id,
        'email': new_user.email,
        'first_name': new_user.first_name,
        'last_name': new_user.last_name,
        'role': new_user.role
    }}), 201


@admin.route('/admin', methods=['GET', 'POST'])
@login_required
def admin_page():

    return render_template("admin.html", user=current_user)


@admin.route('/admin/naudotojai/update-user', methods=['POST'])
@login_required
def update_user():
    data = request.get_json()
    user_id = data.get('user_id')
    email = data.get('email')
    first_name = data.get('first_name')
    role = data.get('role')

    # Update user in the database
    user = User.query.get(user_id)
    if user:
        user.email = email
        user.first_name = first_name
        user.role = role
        db.session.commit()
        return jsonify({'message': 'Naudotojas sėkmingai atnaujintas'}), 200
    else:
        return jsonify({'error': 'Naudotojas nerastas'}), 404


@admin.route('/admin/naudotojai/delete-user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    # Check permissions
    if current_user.role != 'admin':
        return jsonify({"error": "Naudotojas neturi teisių ištrinti naudotojus"}), 403

    user = User.query.get(user_id)

    if not user:
        return jsonify({"error": "Naudotojas nerastas"}), 404

    try:
        # Explicitly remove all associations from the service_employees table
        db.session.execute(
            service_employees.delete().where(service_employees.c.employee_id == user_id)
        )

        # Delete the user from the database
        db.session.delete(user)
        db.session.commit()

        return jsonify({"message": "Naudotojas ištrintas sėkmingai"}), 200
    except Exception as e:
        db.session.rollback()  # Rollback in case of an error
        return jsonify({"error": f"Nepavyko ištrinti naudotojo: {str(e)}"}), 500


@admin.route('/admin/naudotojai/user-details/<int:user_id>', methods=['GET'])
@login_required
def user_details(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'Naudotojas nerastas'}), 404

    return jsonify({
        'id': user.id,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'role': user.role,
    })


@admin.route('/uzsakymai/details/<int:uzsakymas_id>', methods=['GET'])
@login_required
def get_order_details(uzsakymas_id):
    uzsakymas = Uzsakymas.query.get(uzsakymas_id)
    if not uzsakymas:
        return jsonify({'error': 'Apsilankymas nerastas'}), 404

    # Prepare a response object with all necessary details
    response = {
        'id': uzsakymas.id,
        'email': uzsakymas.email,
        'tel_nr': uzsakymas.tel_nr,
        'data': uzsakymas.data,
        'date': uzsakymas.date.strftime('%Y-%m-%d'),
        'time': uzsakymas.time.strftime('%H:%M'),
        'status': uzsakymas.status,
        'employee': f"{uzsakymas.employee.first_name} {uzsakymas.employee.last_name}" if uzsakymas.employee else "N/A",
        'uzsakovas': f"{uzsakymas.first_name} {uzsakymas.last_name}" if uzsakymas.uzsakovas else "N/A",
        'service_id': uzsakymas.service_id,
        'service_name': uzsakymas.service.name if uzsakymas.service else "Unknown Service",
        'created_at': uzsakymas.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        'species': uzsakymas.species,
        'animal_name': uzsakymas.animal_name,
        'symptoms': uzsakymas.symptoms,
        'treatment': uzsakymas.treatment,
    }

    return jsonify(response)


@admin.route('/uzsakymai/update-uzsakymas', methods=['POST'])
@login_required
def update_uzsakymas():
    data = request.get_json()
    uzsakymas_id = data.get('uzsakymas_id')
    uzsakymas = Uzsakymas.query.get(uzsakymas_id)

    if not uzsakymas:
        return jsonify({'error': 'Apsilankymas nerastas'}), 404

    # Update the fields
    uzsakymas.email = data.get('email', uzsakymas.email)
    uzsakymas.tel_nr = data.get('tel_nr', uzsakymas.tel_nr)
    uzsakymas.first_name = data.get('first_name', uzsakymas.first_name)
    uzsakymas.last_name = data.get('last_name', uzsakymas.last_name)
    uzsakymas.service_id = data.get('service_id', uzsakymas.service_id)
    uzsakymas.date = datetime.strptime(data.get('date'), '%Y-%m-%d').date() if data.get('date') else uzsakymas.date
    uzsakymas.status = data.get('status', uzsakymas.status)

    db.session.commit()
    return jsonify({'message': 'Apsilankymo informacija atnaujinta sėkmingai'})


@admin.route('/admin/darbuotojai', methods=['GET', 'POST'])
@login_required
def darbuotojai():
    all_users = User.query.filter_by(role='employee').all()

    if request.method == 'POST':
        user_id = request.form.get('user_id')
        user = User.query.get(user_id)

        if user and user.role == 'employee':
            user.email = request.form.get('email')
            user.first_name = request.form.get('first_name')
            user.role = request.form.get('role')
            db.session.commit()
            flash('Naudotojo informacija sėkmingai atnaujinta!', category='success')
        else:
            flash('Naudotojas nerastas arba neturi leidimo atnaujinti informacijos.', category='error')

    # Return partial content for AJAX requests
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render_template("darbuotojai.html", user=current_user, users=all_users)

    # Otherwise, render a placeholder or redirect to admin
    return redirect('/admin')


@admin.route('/admin/darbuotojai/delete-uzsakymas/<int:uzsakymasId>', methods=['POST'])
@login_required
def delete_darbuotojo_uzsakymas(uzsakymasId):
    uzsakymas = Uzsakymas.query.get(uzsakymasId)

    if uzsakymas:
        db.session.delete(uzsakymas)
        db.session.commit()

    return jsonify({})


@admin.route('/admin/services/manage', methods=['GET'])
@login_required
def manage_services():
    if current_user.role != 'admin':
        abort(403)

    services = Service.query.all()
    categories = Category.query.all()

    return render_template('manage_services.html', services=services, categories=categories)


@admin.route('/admin/services/add-service', methods=['GET', 'POST'])
@login_required
def add_service():
    # Check if the current user is an admin
    if current_user.role != 'admin':
        abort(403)

    if request.method == 'POST':
        # Retrieve form data
        name = request.form.get('name')
        description = request.form.get('description')
        price = request.form.get('price')
        duration = request.form.get('duration')
        category_id = request.form.get('category_id')

        # Validate inputs
        if not (name and description and price and duration and category_id):
            flash('Visi laukai yra būtini.', 'error')
            return redirect(url_for('admin.add_service'))

        # Add service
        try:
            new_service = Service(
                name=name,
                description=description,
                price=float(price),
                duration=int(duration),
                category_id=int(category_id)
            )
            db.session.add(new_service)
            db.session.commit()
            flash('Service added successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Nepavyko pridėti paslaugos.', 'error')
            app.logger.error(f"Klaida pridedant paslaugą: {e}")  # Retain for logging issues
            return redirect(url_for('admin.add_service'))

        return redirect(url_for('admin.admin_page'))

    # Fetch categories for the form
    categories = Category.query.all()
    return render_template('add_service.html', categories=categories)


@admin.route('/admin/services/add-category', methods=['GET', 'POST'])
@login_required
def add_category():
    if current_user.role != 'admin':
        abort(403)

    if request.method == 'POST':
        name = request.form.get('name')

        # Validate inputs
        if not name:
            flash('Būtinas kategorijos pavadinimas.', 'error')
            return redirect(url_for('admin.admin_page'))

        # Check if category already exists
        if Category.query.filter_by(name=name).first():
            flash('Kategorija jau yra.', 'error')
            return redirect(url_for('admin.admin_page'))

        new_category = Category(name=name)
        db.session.add(new_category)
        db.session.commit()

        flash('Kategorija sėkmingai pridėta!', 'success')
        return redirect(url_for('admin.admin_page'))

    # Pass all categories to the template for DataTable rendering
    categories = Category.query.all()
    return render_template('add_category.html', user=current_user, categories=categories)


@admin.route('/admin/services/edit-category', methods=['POST'])
@login_required
def edit_category():
    if current_user.role != 'admin':
        abort(403)

    data = request.get_json()
    category_id = data.get('category_id')
    new_name = data.get('name')

    if not category_id or not new_name:
        return jsonify({'error': 'Neteisinga įvestis'}), 400

    category = Category.query.get(category_id)
    if not category:
        return jsonify({'error': 'Kategorija nerasta'}), 404

    category.name = new_name
    db.session.commit()
    return jsonify({'success': True}), 200


@admin.route('/admin/services/delete-category/<int:category_id>', methods=['POST'])
@login_required
def delete_category(category_id):
    if current_user.role != 'admin':
        abort(403)

    category = Category.query.get(category_id)
    if not category:
        return jsonify({'error': 'kategorija nerasta'}), 404

    db.session.delete(category)
    db.session.commit()
    return jsonify({'success': True}), 200


@admin.route('/admin/services/categories', methods=['GET'])
@login_required
def get_categories():
    categories = Category.query.all()
    return jsonify([{'id': category.id, 'name': category.name} for category in categories])


@admin.route('/admin/services/update', methods=['POST'])
@login_required
def update_service():
    try:
        data = request.get_json()

        # Check if category_id is missing or invalid
        category_id = data.get('category_id')
        if category_id is None:
            return jsonify({'error': 'Kategorijos id negali būti tuščias'}), 400
        category_id = int(category_id)  # Safely cast to int

        # Continue with updating the service
        service_id = data.get('service_id')
        name = data.get('name')
        description = data.get('description')
        price = float(data.get('price'))
        duration = int(data.get('duration'))

        service = Service.query.get(service_id)
        if not service:
            return jsonify({'error': 'Paslaugga nerasta'}), 404

        service.name = name
        service.description = description
        service.price = price
        service.duration = duration
        service.category_id = category_id
        db.session.commit()

        return jsonify({'message': 'Paslauga atnaujinta sėkmingai'}), 200
    except Exception as e:
        return jsonify({'error': f'Nepavyko atnaujinti paslaugos: {str(e)}'}), 500


@admin.route('/admin/services/delete/<int:service_id>', methods=['POST'])
@login_required
def delete_service(service_id):
    # Check permissions
    if current_user.role != 'admin':
        return jsonify({"error": "Naudotojas neturi teisių trinti paslaugoms"}), 403

    service = Service.query.get(service_id)

    if not service:
        return jsonify({"error": "Paslauga nerasta"}), 404

    try:
        db.session.query(Uzsakymas).filter_by(service_id=service_id).delete()

        db.session.execute(
            service_employees.delete().where(service_employees.c.service_id == service_id)
        )

        db.session.delete(service)
        db.session.commit()

        return jsonify({"message": "Paslauga ištrinta sėkmingai"}), 200
    except Exception as e:
        db.session.rollback()  # Rollback in case of an error
        return jsonify({"error": f"Nepavyko ištrinti paslaugos: {str(e)}"}), 500


@admin.route('/admin/services/assign-employees', methods=['POST'])
@login_required
def assign_employees_to_service():
    # Assign employees to a service
    data = request.get_json()
    service_id = data.get('service_id')
    employee_ids = data.get('employee_ids')

    service = Service.query.get(service_id)
    if service:
        service.employees = []  # Clear current assignments
        for employee_id in employee_ids:
            employee = User.query.get(employee_id)
            if employee:
                service.employees.append(employee)
        db.session.commit()
        return jsonify({'message': 'Darbuotojai priskirti paslaugoms sėkmingai'}), 200

    return jsonify({'error': 'Paslauga nerasta'}), 404


@admin.route('/admin/logs')
def view_logs():
    try:
        with open(LOG_FILE, 'r', encoding='utf-8') as log_file:
            logs = log_file.readlines()
    except UnicodeDecodeError:
        with open(LOG_FILE, 'rb') as log_file:
            logs = [line.decode('latin-1') for line in log_file.readlines()]
    except FileNotFoundError:
        logs = ["Žurnalų nerasta."]
    return render_template('logs.html', logs=logs)

