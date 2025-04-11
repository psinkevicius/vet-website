Projekto Aprašymas

Šis projektas skirtas veterinarijos klinikų darbo procesų valdymui ir klientų paslaugų teikimui internetu. Svetainė leidžia:

Rezervuoti vizitus ir valdyti užsakymus

Tvarkyti naudotojų prisijungimus ir registraciją

Administruoti turinį ir naudotojų užklausas

Pateikti aiškų ir patogų naudotojo sąsajos dizainą

Naudotos Technologijos

Programavimo kalba: Python (Flask karkasas)

Duomenų bazė: SQLite

Frontend: HTML, CSS, JavaScript

Diegimo platforma: Heroku

Versijų valdymas: GitHub

Reikalavimai

Prieš paleidžiant projektą, įsitikinkite, kad turite:

Python 3.10.12 (versija nurodyta runtime.txt faile)

Pip – Python paketų valdymo įrankis

Heroku CLI – naudojama diegimui ir valdymui

Diegimo Instrukcija

Klonuokite saugyklą:

git clone https://github.com/psinkevicius/vet-website.git
cd vet-website

Sukurkite virtualią aplinką:

python -m venv venv
source venv/bin/activate  # Linux/MacOS
venv\Scripts\activate   # Windows

ĮDIEKITE priklausomybes:

pip install -r requirements.txt

Paleiskite lokaliai:

flask run

Svetainę rasite http://127.0.0.1:5000

Deploy į Heroku (jei reikia):

heroku login
git push heroku main

Funkcionalumas

Naudotojų registracija ir prisijungimas

Vizitų rezervavimas

Turinio valdymas

Naudotojo sąsajos pritaikymas

Pastabos dėl Diegimo

Duomenų bazė: jei yra migracijų:

heroku run flask db upgrade

Korpora (NLTK): Jei reikia papildomų korporų:

python -m nltk.downloader punkt

Autentifikacija ir Konfigūracija

Google OAuth funkcionalumas naudoja .env konfigūraciją. Sukurkite savo Google OAuth projektą per Google Cloud Console, tada .env faile nurodykite:

OAUTH_CLIENT_ID=YOUR_CLIENT_ID
OAUTH_CLIENT_SECRET=YOUR_CLIENT_SECRET
SECRET_KEY=YOUR_FLASK_SECRET_KEY
MAIL_USERNAME=YOUR_EMAIL
MAIL_PASSWORD=YOUR_EMAIL_PASSWORD_OR_APP_PASSWORD

Svarbu: įtraukite .env į .gitignore failą, kad jis nebūtų atsitiktinai paviešintas.

Testavimas:

Vienetinis testavimas atliktas siekiant užtikrinti stabilumą

Rankiniai testai padėjo aptikti ir pašalinti klaidas

Nuorodos:

Svetainė: https://saugi-peda-656eb4263c6b.herokuapp.com/

Saugykla: gitHub




