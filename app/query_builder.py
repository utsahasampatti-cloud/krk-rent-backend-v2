from urllib.parse import urlencode, quote_plus
from app.schemas import Filters
from app.settings import settings


def _city_slug(city: str) -> str:
    # MVP: підтримуємо тільки Kraków як “залізний” кейс
    c = city.strip().lower()
    if c in ("kraków", "krakow"):
        return "krakow"
    # якщо дадуть інше — все одно зберемо slug грубо (без гарантій)
    return quote_plus(c)


def build_olx_url(filters: Filters) -> str:
    """
    ЄДИНЕ джерело правди для OLX URL.

    Примітка (MVP): districts/rooms додаємо як текстовий query (q-...) + price_max як query param.
    Навіть якщо OLX змінить фільтри, URL не “ламається”, максимум фільтр буде проігнорований.
    """
    city_slug = _city_slug(filters.city)
    base = f"{settings.OLX_BASE_URL}/nieruchomosci/mieszkania/wynajem/{city_slug}/"

    keywords = []
    if filters.rooms:
        keywords.append(f"{filters.rooms} pokoje")
    for d in (filters.districts or []):
        d = d.strip()
        if d:
            keywords.append(d)

    path = base
    if keywords:
        q = "-".join(quote_plus(k).replace("+", "-") for k in keywords)
        path = f"{base}q-{q}/"

    params = {}
    if filters.price_max:
        # Часто працює на OLX як стандартний параметр ціни
        params["search[filter_float_price:to]"] = str(filters.price_max)

    if params:
        return f"{path}?{urlencode(params)}"
    return path
