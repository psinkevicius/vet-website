from flask import Blueprint, render_template, request, flash, url_for
from . import db, oauth
from .models import User, Feedback
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, login_required, logout_user, current_user
from datetime import datetime, timedelta
import uuid
from . import mail
from flask_mail import Message
from flask import redirect
from flask import current_app as app
from .utils import is_valid_email, is_strong_password

auth = Blueprint('auth', __name__, template_folder='templates/auth_templates')


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if not email or not password:
            return redirect(url_for('auth.login'))

        user = User.query.filter_by(email=email).first()

        if user:
            if check_password_hash(user.password, password):
                flash('Prisijungta sėkmingai!', category='success')
                login_user(user, remember=True)

                # Log successful login
                app.logger.info(f"User {user.id} logged in successfully with email: {email}")

                return redirect(url_for('auth.home'))
            else:
                flash('Neteisingas slaptažodis, bandykitė vėl.', category='error')

                # Log failed login due to incorrect password
                app.logger.warning(f"Nepavyko prisijungti vartotojui {user.id}: Neteisingas slaptažodis")
        else:
            flash('El. pašto adresas neegzistuoja', category='error')

            # Log failed login due to non-existent email
            app.logger.warning(f"Nepavyko prisijungti prie neegzistuojančio el. pašto adreso: {email}")

    return render_template("login.html", user=current_user)


@auth.route('/logout')
@login_required
def logout():
    user_email = current_user.email  # Get the user email before logging out
    logout_user()

    # Log the logout action with the user email
    app.logger.info(f"Naudotojas su el. paštu {user_email} atsijungė sėkmingai")

    return redirect(url_for('auth.login'))


@auth.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        email = request.form.get('email')
        first_name = request.form.get('firstName')
        last_name = request.form.get('lastName')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')
        role = request.form.get('role', 'customer')

        # Log and redirect if the email is invalid (HTML doesn't catch all invalid emails)
        if not is_valid_email(email):
            app.logger.warning(f"Bandymas prisiregistruoti netinkamu el. pašto formatu: {email}")
            return redirect(url_for('auth.sign_up'))

        # Check if email is already registered
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            app.logger.warning(f"Bandymas prisiregistruoti naudojant esamą el: {email}")
            flash('El. pašto adresas jau yra.', category='error')
            return redirect(url_for('auth.sign_up'))

        # Check password strength
        if not is_strong_password(password1):
            app.logger.warning(f"Silpno slaptažodžio bandymas el. paštu: {email}")
            flash('Slaptažodį turi sudaryti mažiausiai 8 simboliai, jame turi būti didžiosios, mažosios raidės, skaičiai ir specialieji simboliai.', category='error')
            return redirect(url_for('auth.sign_up'))

        # Check if passwords match
        if password1 != password2:
            app.logger.warning(f"Slaptažodžio neatitikimas bandant prisiregistruoti el. paštu: {email}")
            flash('Slaptažodžiai nesutampa.', category='error')
            return redirect(url_for('auth.sign_up'))

        # Create the user and log successful account creation
        hashed_password = generate_password_hash(password1, method='pbkdf2:sha256')
        new_user = User(email=email, first_name=first_name, last_name=last_name, password=hashed_password, role=role)
        db.session.add(new_user)
        db.session.commit()

        app.logger.info(f"Nauja paskyra sėkmingai sukurta el. paštui: {email}")
        flash('Paskyra sėkmingai sukurta!', category='success')
        return redirect(url_for('auth.home'))

    return render_template("sign_up.html", user=current_user)


@auth.route('/login/google')
def google_login():
    redirect_uri = url_for('auth.google_callback', _external=True)
    return oauth.google.authorize_redirect(redirect_uri)


@auth.route('/login/google/callback')
def google_callback():
    try:
        # Step 1: Exchange authorization code for access token
        token = oauth.google.authorize_access_token()

        # Step 2: Fetch user information
        user_info = oauth.google.get('https://openidconnect.googleapis.com/v1/userinfo').json()

        # Step 3: Validate required user information
        if not user_info or not user_info.get('email') or not user_info.get('sub'):
            flash('Nepavyko prisijungti prie Google. Trūksta vartotojo informacijos.', category='error')
            return redirect(url_for('auth.login'))

        # Step 4: Check if user already exists
        user = User.query.filter_by(email=user_info['email']).first()

        if user:
            # If user exists, log them in
            login_user(user)
            flash('Sėkmingai prisijungėte prie Google!', category='success')
        else:
            # If user does not exist, create a new account
            user = User(
                email=user_info['email'],
                first_name=user_info.get('given_name', 'Unknown'),
                last_name=user_info.get('family_name', ''),
                google_id=user_info['sub'],
                google_picture=user_info.get('picture', ''),
                password='',  # Leave password blank for OAuth users
                role='customer'  # Default role
            )
            db.session.add(user)
            db.session.commit()
            login_user(user)
            flash('Nauja paskyra sėkmingai sukurta ir prisijungta per Google!', category='success')

        # Step 6: Redirect to the home page
        return redirect(url_for('auth.home'))

    except Exception as e:
        app.logger.error(f"Nepavyko prisijungti prie Google: {e}")
        flash(f'Nepavyko prisijungti prie Google: {str(e)}', category='error')
        return redirect(url_for('auth.login'))


@auth.route('/leave-feedback', methods=['GET', 'POST'])
@login_required
def leave_feedback():
    if request.method == 'POST':
        comment = request.form.get('comment')
        rating = request.form.get('rating')

        if not comment or not rating:
            flash('Visi laukai yra būtini!', category='error')
            return redirect(url_for('auth.leave_feedback'))

        feedback = Feedback(
            author_id=current_user.id,
            comment=comment,
            rating=int(rating),
        )
        db.session.add(feedback)
        db.session.commit()
        flash('Atsiliepimai sėkmingai pateikti!', category='success')
        return redirect(url_for('auth.home'))

    return render_template('leave_feedback.html', user=current_user)


@auth.route('/')
def home():
    feedbacks = Feedback.query.order_by(Feedback.date_posted.desc()).limit(6).all()
    return render_template('home.html', feedbacks=feedbacks, user=current_user)


@auth.route('/apie-mus')
def apie_mus():
    return render_template('about_us.html', user=current_user)


@auth.route('/logout/google')
def google_logout():
    logout_user()
    return redirect(url_for('auth.login'))


@auth.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()

        # Log if the email is not found in the database
        if not user:
            app.logger.warning(f"Neegzistuojančio el. pašto slaptažodžio nustatymo iš naujo bandymas: {email}")
            flash("El. pašto adresas nerastas. Bandykite dar kartą.", "danger")
            return redirect(url_for('auth.forgot_password'))

        # Generate a unique reset token and expiration time
        user.reset_token = str(uuid.uuid4())
        user.reset_token_expiration = datetime.utcnow() + timedelta(hours=1)
        db.session.commit()

        # Construct the reset link
        reset_link = url_for('auth.verify_code', token=user.reset_token, _external=True)

        # Send the email with the reset link
        msg = Message("Slaptažodžio nustatymo iš naujo užklausa", sender="kenkikenkitor@gmail.com", recipients=[email])
        msg.body = f"Sveiki, norėdami iš naujo nustatyti slaptažodį, naudokite šią nuorodą: {reset_link}"
        mail.send(msg)

        # Log that the reset link was successfully sent
        app.logger.info(f"Slaptažodžio nustatymo iš naujo nuoroda išsiųsta el. paštu: {email}")

        flash("Atkūrimo nuoroda išsiųsta jūsų el. paštu.", "info")
        return redirect(url_for('auth.login'))

    return render_template('forgot_password.html', user=current_user)


@auth.route('/verify-code/<token>', methods=['GET', 'POST'])
def verify_code(token):
    user = User.query.filter_by(reset_token=token).first()

    # Check if token is valid and not expired
    if user is None or user.reset_token_expiration < datetime.utcnow():
        app.logger.warning(f"Neteisingas arba pasibaigęs slaptažodžio nustatymo iš naujo prieigos raktas bandymas: {token}")
        flash("Nustatyti iš naujo nuoroda neteisinga arba pasibaigė.", "danger")
        return redirect(url_for('auth.forgot_password'))

    if request.method == 'POST':
        new_password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        # Ensure passwords match
        if new_password != confirm_password:
            app.logger.warning(f"Bandymas neatitikti slaptažodžio nustatymo iš naujo prieigos rakto: {token}")
            flash("Slaptažodžiai nesutampa.", "danger")
            return redirect(url_for('auth.verify_code', token=token))

        # Hash and save the new password
        user.password = generate_password_hash(new_password)
        user.reset_token = None  # Clear the reset token
        user.reset_token_expiration = None  # Clear the token expiration
        db.session.commit()  # Commit the changes to the database

        app.logger.info(f"Sėkmingai iš naujo nustatytas el. pašto slaptažodis: {user.email}")
        flash("Jūsų slaptažodis sėkmingai nustatytas iš naujo.", "success")
        return redirect(url_for('auth.login'))

    return render_template('verify_code.html', user=current_user)






