import requests

FALLBACK_QUOTES = [
    '"Het enige wat telt is wat je doet, niet wat je zegt." — Anoniem',
    '"Kleine stappen zijn nog steeds stappen vooruit." — Anoniem',
    '"Discipline is doen wat gedaan moet worden, ook als je er geen zin in hebt." — Anoniem',
    '"Je hoeft niet perfect te zijn om te beginnen." — Anoniem',
    '"Consistentie verslaat motivatie op de lange termijn." — Anoniem',
]

_fallback_index = 0


def get_quote() -> str:
    global _fallback_index
    try:
        response = requests.get("https://zenquotes.io/api/random", timeout=10)
        response.raise_for_status()
        data = response.json()
        quote = data[0]["q"]
        author = data[0]["a"]
        return f'"{quote}" — {author}'
    except Exception:
        quote = FALLBACK_QUOTES[_fallback_index % len(FALLBACK_QUOTES)]
        _fallback_index += 1
        return quote
