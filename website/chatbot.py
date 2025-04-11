from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import current_user
from nltk.chat.util import Chat, reflections
from flask import jsonify

pairs = [
    ["mano augintinio vardas yra (.*)", ["Supratau, jūsų augintinio vardas yra %1. Kaip galiu jums padėti dėl jo?"]],
    ["labas", ["Sveiki, kuom galėčiau jums padėti?"]],
    ["mano užsakymo numeris yra (.*)", ["Puiku, jūsų užsakymo numeris yra %1. Patikrinsiu informaciją apie užsakymą."]],
    ["kaip galiu atšaukti susitikimą (.*)", ["Norint atšaukti susitikimą, prašome pateikti susitikimo numerį arba datą."]],
    ["kada bus kitas mano augintinio susitikimas (.*)", ["Jūsų augintinio kitas susitikimas numatytas %1. Jei norite pakeisti datą, praneškite."]],
    ["kaip galiu pakeisti savo kontaktinę informaciją (.*)", ["Jūsų kontaktinę informaciją galima pakeisti prisijungus prie jūsų paskyros ir atnaujinant duomenis."]],
    ["mano augintinis turi problemų su (.*)", ["Aprašykite simptomus arba problemą %1, ir mes pasiūlysime tinkamą gydymą ar susitikimą su specialistu."]],
    ["ar teikiate skiepų paslaugas (.*)", ["Taip, mes teikiame skiepų paslaugas. Prašome susisiekti su mumis dėl rezervacijos."]],
    ["kaip galiu gauti savo augintinio medicininę istoriją (.*)", ["Jūsų augintinio medicininę istoriją galite gauti prisijungus prie savo paskyros arba apsilankius klinikoje."]],
    ["kada dirbate (.*)", ["Mūsų darbo laikas yra nuo pirmadienio iki penktadienio, 9:00–17:00, o šeštadieniais 10:00–14:00."]],
    ["mano augintinis turi alergiją (.*)", ["Ačiū, kad informavote. Prašome pateikti daugiau informacijos apie alergiją %1, kad galėtume pasiūlyti tinkamą sprendimą."]],
    ["ar galite pasiūlyti dietą mano augintiniui (.*)", ["Žinoma, galime pateikti individualizuotas mitybos rekomendacijas jūsų augintiniui %1."]],
    ["ar galite patikrinti mano augintinio būklę (.*)", ["Taip, mes galime atlikti sveikatos patikrinimą. Susitarkite dėl apsilankymo per mūsų svetainę ar telefonu."]],
    ["mano augintinis yra (.*)", ["Supratau, jūsų augintinis yra %1. Kaip galime jums padėti dėl jo?"]],
    ["kaip galiu gauti receptą (.*)", ["Receptą galite gauti po susitikimo su veterinaru. Rezervuokite susitikimą internetu arba telefonu."]],
    ["ar galite man pasakyti apie dažniausias augintinių ligas (.*)", ["Žinoma, galiu suteikti informacijos apie dažniausias augintinių ligas, pvz., odos problemas, alergijas ar parazitines infekcijas."]],
    ["kaip galiu patikrinti savo užsakymo būseną (.*)", ["Užsakymo būseną galite patikrinti prisijungę prie savo paskyros arba susisiekę su mūsų komanda."]],
    ["ar galite rekomenduoti prevencines priemones (.*)", ["Taip, prevencinės priemonės, tokios kaip skiepai, antiparazitiniai preparatai ir sveika mityba, yra labai svarbios."]],
    ["ar priimate naujus klientus (.*)", ["Taip, mes mielai priimsime naujus klientus. Prašome užsiregistruoti mūsų svetainėje arba telefonu."]],
    ["kada man reikėtų sterilizuoti savo augintinį (.*)", ["Sterilizacija paprastai rekomenduojama, kai augintinis yra 6–12 mėnesių amžiaus. Tačiau tai priklauso nuo augintinio būklės."]],
    ["kaip galiu užsiregistruoti vizitui (.*)", ["Vizitą galite užregistruoti internetu arba susisiekę su mumis telefonu."]],
    ["mano augintinis įkando (.*)", ["Ačiū už informaciją. Prašome kreiptis į veterinarą, kad būtų įvertinta situacija."]],
    ["ar galite suteikti pagalbą nelaimės atveju (.*)", ["Taip, mes teikiame pagalbą nelaimės atveju. Prašome nedelsiant skambinti mūsų avarinei linijai."]],
    ["ar galite padėti su augintinio dresūra (.*)", ["Taip, galime pateikti rekomendacijas arba nukreipti jus į specialistus."]],
    ["ką daryti, jei mano augintinis prarado apetitą (.*)", ["Jei jūsų augintinis prarado apetitą %1, prašome pasitarti su veterinaru, nes tai gali reikšti sveikatos problemas."]],
    ["mano augintinis per daug kasosi (.*)", ["Nuolatinis kasymasis gali rodyti alergijas ar odos problemas. Prašome rezervuoti vizitą patikrinimui."]],
    ["kokių dokumentų man reikės vizitui (.*)", ["Vizitui užtenka atnešti augintinio medicininius dokumentus, jei turite, ir pateikti pagrindinę informaciją."]],
    ["ar galite suteikti daugiau informacijos apie mano augintinio sveikatą (.*)", ["Taip, mes galime aptarti jūsų augintinio sveikatą ir suteikti patarimų, remiantis jo medicinine istorija."]],
    ["kaip galiu atnaujinti savo augintinio duomenis (.*)", ["Savo augintinio duomenis galite atnaujinti prisijungę prie paskyros arba apsilankę mūsų klinikoje."]],
    ["mano augintinis yra sužeistas (.*)", ["Ačiū, kad informavote. Nedelsdami kreipkitės į veterinarą arba apsilankykite mūsų klinikoje."]],
    ["ačiū", ["Prašome! Jei turėsite daugiau klausimų, nedvejokite kreiptis."]],
]


def start_chat(user_input):
    chat = Chat(pairs, reflections)
    response = chat.respond(user_input)
    if response:
        return response
    else:
        # Default response if no match is found
        return "Nežinau atsakymo į šį klausimą, susiekite su administracija kenkikenkitor@gmail.com arba telefonu +37064745739."


chatbot = Blueprint('chatbot', __name__)


@chatbot.route('/chatbot', methods=['POST'])
def start_page():
    if request.method == 'POST':
        user_input = request.json.get('user_input')
        if user_input:
            bot_response = start_chat(user_input)
            return jsonify(response=bot_response)
        return jsonify(response="Nežinau atsakymo į šį klausimą, susiekite su administracija kenkikenkitor@gmail.com arba telefonu +37064745739.")



