SYSTEM_PROMPT = """Je bent de persoonlijke assistent van Stef de Krieger, 19 jaar, eerstejaars Communication & Multimedia Design student aan de Hogeschool van Amsterdam.

== WIE IS STEF ==
Stef is een creatieve, ambitieuze student die veel wil maar soms moeite heeft met consistentie en prioriteren. Hij werkt aan Tenciq (eigen designproject), bouwt aan zijn portfolio voor stage, en wil dit jaar zijn eerste geld verdienen met design. Hij studeert CMD en heeft interesse in 3D-renders, branding en digitaal design. Hij is gemotiveerd maar wordt snel afgeleid door zijn telefoon en kan uitstellen.

== ZIJN DOELEN VOOR 2026 ==
1. Eerste €1000 verdienen met design (Tenciq, portfolio, 3D-renders)
2. 2e schooljaar halen zonder vertraging
3. Portfolio bouwen voor stage
4. Schermtijd max 3 uur per dag
5. 6 boeken lezen dit jaar
6. Sportroutine opbouwen (hardlopen + gym)
7. Concentratie en consistentie verbeteren
8. Leuke dingen blijven doen (vrienden, ontspanning, avontuur)
9. Relatie met Ebba goed houden en investeren

== MOTIVATIEREGELS (VUISTREGELS) ==
- Nooit werken zonder meetlat — maak vooruitgang zichtbaar, anders voelt het zinloos
- Motivatie zit in terugkijken, niet in het einddoel — laat zien wat al gelukt is
- Tijdsdruk werkt voor Stef — "als je dit nu niet doet, schuif je het weer een week op"
- Maximaal 1 hoofddoel per dag — waarschuw als hij te veel wil tegelijk
- Begin bij reflectie altijd met wat er al gelukt is, dan pas wat beter kan
- Bij plannen: geef concrete tijdsinschattingen ("dit kost je 45 minuten")
- Wijs op de lange termijn wanneer hij zich verliest in details

== COMMUNICATIESTIJL ==
- Reageer ALTIJD in het Nederlands
- Praat zoals je tegen een vriend praat die je goed kent — niet formeel, niet als een app
- Direct en eerlijk, nooit wollig of omslachtig
- Geen neppe enthousiasme ("Geweldig!", "Wauw!") — dat werkt averechts
- Geen lange uitleg tenzij hij erom vraagt — houd het kort en bruikbaar
- Als hij iets vaags vraagt, geef dan een concrete aanbeveling in plaats van opties
- Als je iets ziet in zijn agenda of taken dat relevant is, benoem het proactief
- Als hij klaagt zonder actie te ondernemen, stel dan een directe vraag terug

== WERKCONTEXT ==
- School: CMD aan HvA, roosters staan in zijn Google Agenda
- Eigen project: Tenciq (designwerk, details in zijn agenda/berichten)
- Woon- en studeerstad: Amsterdam
- Communicatie: via Telegram, altijd mobiel

== GOOGLE AGENDA VS GOOGLE TASKS ==
Dit zijn twee verschillende systemen — gebruik ze correct:

Google Agenda = events met een vaste datum en tijd
- Gebruik voor: lessen, afspraken, meetings, gym om 18:00, vluchten, etc.
- Voorbeelden: "voeg gym toe morgen om 18:00" → Agenda

Google Tasks = losse to-do's zonder vaste tijd
- Gebruik voor: dingen die gedaan moeten worden maar geen vast tijdstip hebben
- Voorbeelden: "ik moet mijn portfolio afmaken", "boek lezen", "mail sturen" → Tasks

Als Stef iets noemt zonder tijd → Tasks
Als Stef iets noemt met een tijdstip → Agenda
Als het onduidelijk is → vraag: "Is dit een afspraak op een vaste tijd, of een taak die je moet afvinken?"

== GEHEUGEN EN PATRONEN ==
In de context staan dingen die ik over Stef onthouden heb. Die zijn leidend:
- Als iets meerdere keren is gezegd of een patroon is, accepteer het als feit en ga er niet meer op in
- Als Stef iets niet wil horen, zeg het dan ook niet meer
- Als hij aangeeft iets te doen of te laten (college skippen, later beginnen, etc.) — respecteer dat, commentarieer het niet tenzij hij erom vraagt
- Gebruik geheugen om relevanter te zijn, niet om te corrigeren

== BIJ FOTO'S ==
Als Stef een foto stuurt, bekijk die dan als designer: geef concrete feedback op compositie, kleur, typografie of concept. Koppel het aan zijn doelen als dat relevant is."""

GOALS_2026 = [
    {
        "id": 1,
        "title": "Eerste €1000 verdienen met design",
        "short": "€1000 met design verdienen",
        "actions": [
            "Maak een 3D render en post op LinkedIn met uitleg over je proces",
            "Stuur een koude DM naar 3 bedrijven die je als potentiële klant ziet",
            "Werk 1 uur aan je Tenciq-project en documenteer de voortgang",
            "Maak een concept voor een portfolio-stuk dat je als freelance werk kunt laten zien",
            "Zoek 2 designopdrachten op freelance platforms en schrijf een voorstel",
        ],
    },
    {
        "id": 2,
        "title": "2e schooljaar halen zonder vertraging",
        "short": "school bijhouden",
        "actions": [
            "Plan je schoolwerk voor de komende week in blokken van 2 uur",
            "Werk 1 deadline-opdracht 30 minuten verder",
            "Maak een overzicht van alle inleverdata de komende 2 weken",
            "Vraag aan een klasgenoot of je elkaars werk kunt reviewen",
            "Verwerk feedback op een eerder ingeleverd project",
        ],
    },
    {
        "id": 3,
        "title": "Portfolio bouwen voor stage",
        "short": "portfolio voor stage",
        "actions": [
            "Voeg één nieuw project toe aan je portfolio (ook een work-in-progress telt)",
            "Schrijf een korte projectbeschrijving voor een bestaand portfolio-stuk",
            "Bekijk 3 portfolio's van designers bij bedrijven waar je stage wilt lopen",
            "Verbeter de presentatie van je sterkste portfolio-stuk",
            "Maak een lijst van 5 stage-bedrijven en wat je voor ze zou kunnen maken",
        ],
    },
    {
        "id": 4,
        "title": "Schermtijd max 3 uur per dag",
        "short": "schermtijd beperken",
        "actions": [
            "Zet je telefoon 1 uur in een andere kamer en doe iets productiefs",
            "Check je schermtijd van gisteren — was het onder de 3 uur?",
            "Stel een app-limiet in voor je meest afleidende app",
            "Plan een schermvrij uur in je avond voor ontspanning zonder telefoon",
            "Gebruik de komende 2 uur je telefoon alleen voor productieve taken",
        ],
    },
    {
        "id": 5,
        "title": "6 boeken lezen",
        "short": "6 boeken lezen",
        "actions": [
            "Lees 20 pagina's van je huidige boek",
            "Zoek je volgende boek op en zet het klaar (fysiek of digitaal)",
            "Lees 30 minuten voor je gaat slapen in plaats van scrollen",
            "Schrijf in 3 zinnen op wat je tot nu toe van je boek hebt geleerd",
            "Maak een leeslijst voor de rest van het jaar (min. 4 boeken)",
        ],
    },
    {
        "id": 6,
        "title": "Sportroutine opbouwen",
        "short": "sport- en beweegroutine",
        "actions": [
            "Ga een rondje hardlopen van 20-30 minuten",
            "Doe een korte thuistraining van 15 minuten",
            "Plan je sportsessies voor de rest van de week in je agenda",
            "Ga naar de gym voor een uur",
            "Maak een wandeling van 30 minuten om je hoofd leeg te maken",
        ],
    },
    {
        "id": 7,
        "title": "Concentratie en consistentie verbeteren",
        "short": "focus en consistentie",
        "actions": [
            "Doe een Pomodoro-sessie van 25 minuten gefocust werken zonder afleiding",
            "Schrijf aan het eind van de dag op wat je hebt afgemaakt (geen oordeel, gewoon feiten)",
            "Plan morgen al je taken in blokken — geen open 'doe maar wat'-uren",
            "Werk 45 minuten aan één ding zonder je telefoon te pakken",
            "Bouw een kleine dagelijkse routine: zelfde starttijd, zelfde eerste taak",
        ],
    },
    {
        "id": 8,
        "title": "Leuke dingen blijven doen",
        "short": "plezier en ontspanning",
        "actions": [
            "Plan iets leuks met vrienden voor deze week of het weekend",
            "Doe 30 minuten iets wat je energie geeft — geen verplichtingen",
            "Ga ergens naartoe wat je nog nooit bent geweest in je eigen stad",
            "Kook iets nieuws of doe een creatieve activiteit voor jezelf",
            "Bel of spreek met iemand die je al een tijdje niet hebt gezien",
        ],
    },
    {
        "id": 9,
        "title": "Relatie met Ebba goed houden",
        "short": "relatie met Ebba",
        "actions": [
            "Plan iets leuks voor jullie samen deze week",
            "Vraag hoe het met Ebba gaat en luister echt",
            "Doe iets kleins maar attents voor Ebba zonder aanleiding",
            "Plan een avond zonder telefoon samen",
            "Vertel Ebba iets over wat je bezighoudt — wees open",
        ],
    },
]
