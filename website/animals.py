from flask import Blueprint, render_template, request, flash, jsonify, url_for
from . import db
from .models import Uzsakymas, Animal
from flask_login import login_required, current_user
from flask import redirect
from flask import current_app as app
from .utils import get_user_by_id

animals = Blueprint('animals', __name__, template_folder='templates/animals_templates')


@animals.route('/add-animal', methods=['GET', 'POST'])
@login_required
def add_animal():
    if request.method == 'POST':
        name = request.form.get('name')
        species = request.form.get('species')

        if not name or not species:
            flash('Reikalingas pavadinimas ir rūšis!', category='error')
            return redirect(url_for('animals.add_animal'))

        new_animal = Animal(name=name, species=species, owner_id=current_user.id)
        db.session.add(new_animal)
        db.session.commit()
        flash('Augintinis pridėtas sėkmingai!', category='success')
        return redirect(url_for('animals.my_animals'))

    return render_template('my_animals.html')


@animals.route('/my-animals', methods=['GET'])
@login_required
def my_animals():
    page = request.args.get('page', 1, type=int)  # Current page number, default to 1
    per_page = 2  # Number of animals per page
    search_query = request.args.get('search', '').strip()  # Search query, default is empty

    # Build the base query for animals
    base_query = Animal.query.filter_by(owner_id=current_user.id)

    # Apply the search filter
    if search_query:
        base_query = base_query.filter(
            db.or_(
                Animal.name.ilike(f"%{search_query}%"),  # Search by animal name
                Animal.species.ilike(f"%{search_query}%")  # Search by species
            )
        )

    # Paginate the filtered query
    paginated_animals = base_query.paginate(page=page, per_page=per_page)

    return render_template(
        'my_animals.html',
        animals=paginated_animals.items,  # Only the animals for the current page
        pagination=paginated_animals,  # The pagination object
        search_query=search_query,  # Pass the search query to the template
        user=current_user
    )


@animals.route('/animal-history/<int:animal_id>', methods=['GET'])
@login_required
def animal_history(animal_id):
    animal = Animal.query.filter_by(id=animal_id, owner_id=current_user.id).first_or_404()
    appointments = Uzsakymas.query.filter_by(animal_id=animal_id).order_by(Uzsakymas.date.desc()).all()
    return render_template('animal_history.html', user=current_user, animal=animal, appointments=appointments, get_user_by_id=get_user_by_id)


@animals.route('/animals/delete/<int:animal_id>', methods=['POST'])
@login_required
def delete_animal(animal_id):
    animal = Animal.query.filter_by(id=animal_id, owner_id=current_user.id).first()
    if not animal:
        return jsonify({"error": "Augintinis nerastas arba jūs neturite leidimo jo ištrinti."}), 404

    try:
        has_pending_appointments = any(appointment.status == "Vykdoma" for appointment in animal.appointments)
        if has_pending_appointments:
            return jsonify({"error": "Negalima ištrinti gyvūno su vykdomais apsilankymais."}), 400

        db.session.delete(animal)
        db.session.commit()
        return jsonify({"message": "Augintinis ištrintas teisingai"}), 200
    except Exception as e:
        app.logger.error(f"Klaida trinant augintinį: {e}")
        return jsonify({"error": "Įvyko netikėta klaida. Bandykite dar kartą."}), 500
