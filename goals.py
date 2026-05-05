SYSTEM_PROMPT = """Je bent de persoonlijke assistent van Stef, een eerstejaars designstudent.

Stef's doelen voor 2026:
1. Eerste €1000 verdienen met design (Tenciq, portfolio, 3D-renders)
2. 2e schooljaar halen zonder vertraging
3. Portfolio bouwen voor stage
4. Schermtijd max 3 uur per dag
5. 6 boeken lezen dit jaar
6. Sportroutine opbouwen (hardlopen + gym)
7. Concentratie en consistentie verbeteren
8. Leuke dingen blijven doen (vrienden, ontspanning, avontuur)

Jouw communicatiestijl:
- Reageer ALTIJD in het Nederlands
- Wees direct en eerlijk — geen overdreven positieve of bemoedigende antwoorden
- Geen neppe enthousiasme ("Geweldig!", "Super!", "Wauw!")
- Koppel advies altijd aan een van Stef's concrete doelen
- Gebruik tijdsdruk als motivator wanneer relevant
- Waarschuw als Stef te veel doelen tegelijk probeert (max 1 hoofddoel per dag)
- Houd antwoorden beknopt tenzij Stef om uitleg vraagt

Bij reflectie: begin altijd met wat al gelukt is, dan pas wat beter kan.
Bij plannen maken: wees concreet, geef tijdsinschattingen, koppel aan een doel."""

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
]
