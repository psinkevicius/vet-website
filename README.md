Veterinarijos Klinikos Internetinė Svetainė Projekto Aprašymas Šis projektas skirtas veterinarijos klinikų darbo procesų valdymui ir klientų paslaugų teikimui internetu. Svetainė leidžia:

Rezervuoti vizitus ir valdyti užsakymus. Tvarkyti naudotojų prisijungimus ir registraciją. Administruoti turinį ir naudotojų užklausas. Pateikti aiškų ir patogų naudotojo sąsajos dizainą. Naudotos Technologijos Programavimo kalba: Python (Flask karkasas) Duomenų bazė: SQLite Frontend: HTML, CSS, JavaScript Diegimo platforma: Heroku Versijų valdymas: GitHub Reikalavimai Prieš paleidžiant projektą, įsitikinkite, kad turite:

Python 3.10.12 (versija nurodyta runtime.txt faile). Pip – Python paketų valdymo įrankis. Heroku CLI – naudojama diegimui ir valdymui. Diegimo Instrukcija Klonuokite saugyklą:

bash Copy code git clone https://github.com/vikoeif/pi21-masterajj.git cd pi21-masterajj Sukurkite virtualią aplinką:

bash Copy code python -m venv venv source venv/bin/activate # Linux/MacOS venv\Scripts\activate # Windows Įdiekite priklausomybes:

bash Copy code pip install -r requirements.txt Paleiskite lokaliai:

bash Copy code flask run Svetainę rasite http://127.0.0.1:5000.

Deploy į Heroku (jei reikia):

bash Copy code heroku login git push heroku main Funkcionalumas Naudotojų registracija ir prisijungimas. Vizitų rezervavimas. Turinio valdymas. Naudotojų sąsajos pritaikymas. Pastabos dėl Diegimo Duomenų bazė: Paleiskite šią komandą Heroku aplinkoje, jei yra migracijų: bash Copy code heroku run flask db upgrade Korpora (NLTK): Jei reikia papildomų korporų: bash Copy code python -m nltk.downloader punkt Testavimas Vienetinis testavimas atliktas siekiant užtikrinti stabilumą. Rankiniai testai padėjo aptikti ir pašalinti klaidas. Nuorodos Svetainė: https://saugi-peda-656eb4263c6b.herokuapp.com/ Saugykla: GitHub Licencija Šis projektas yra viešas ir atviras naudoti mokymosi ir nekomerciniais tikslais.

Projekte pateiktas `client_secret.json` failas naudoja **pavyzdinius (placeholder) duomenis** saugumo sumetimais.

Jeigu norite naudotis Google OAuth funkcionalumu, turite susikurti savo `client_secret.json` per Google Cloud Console ir pakeisti laukus `client_id`, `client_secret`, `project_id` į savo.

```json
{
  "web": {
    "client_id": "YOUR_CLIENT_ID_HERE",
    "project_id": "YOUR_PROJECT_ID_HERE",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_secret": "YOUR_CLIENT_SECRET_HERE",
    "redirect_uris": ["http://127.0.0.1:5000"],
    "javascript_origins": ["http://127.0.0.1:5000"]
  }
}

Šiame projekte visos jautrios konfigūracijos vertės (pvz., SECRET_KEY, MAIL_USERNAME, MAIL_PASSWORD, client_secret.json failas) yra pakeistos pavyzdiniais duomenimis dėl saugumo priežasčių.
