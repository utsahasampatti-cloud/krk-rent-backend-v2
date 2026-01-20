import re
from typing import Dict, List, Optional
from urllib.parse import urljoin

import httpx
from selectolax.parser import HTMLParser

from app.settings import settings


_PRICE_RE = re.compile(r"([\d\s]+)")


def _parse_price(text: str) -> Optional[float]:
    if not text:
        return None
    m = _PRICE_RE.search(text.replace("\xa0", " "))
    if not m:
        return None
    digits = m.group(1).replace(" ", "").strip()
    if not digits:
        return None
    try:
        return float(digits)
    except Exception:
        return None


def _extract_listings(html: str) -> List[Dict]:
    tree = HTMLParser(html)
    items: List[Dict] = []

    # OLX UI міняється, тому беремо максимально “м’які” селектори:
    # - посилання на оголошення
    # - заголовок
    for a in tree.css("a"):
        href = a.attributes.get("href", "") or ""
        if not href:
            continue
        # типово оголошення має /d/oferta/...
        if "/d/oferta/" not in href:
            continue

        url = href if href.startswith("http") else urljoin(settings.OLX_BASE_URL, href)

        title = (a.text() or "").strip()
        if not title or len(title) < 6:
            # інколи title не прямо в <a>, тоді пробуємо знайти ближчий заголовок
            h = a.css_first("h6") or a.css_first("h5") or a.css_first("h4")
            if h:
                title = (h.text() or "").strip()

        # пробуємо знайти ціну поряд
        price = None
        # дивимось на батьківський контейнер: часто ціна поруч
        parent = a.parent
        if parent:
            txt = parent.text(separator=" ").replace("\xa0", " ")
            # шукаємо "zł"
            if "zł" in txt:
                # беремо фрагмент біля zł
                idx = txt.find("zł")
                frag = txt[max(0, idx - 30): idx + 10]
                price = _parse_price(frag)

        # локація часто є в картці (місто/район + дата)
        location = None
        if parent:
            # пробуємо по "Kraków," патерну, якщо є
            txt = parent.text(separator=" ").replace("\xa0", " ")
            if "Kraków" in txt:
                # виріжемо коротко
                pos = txt.find("Kraków")
                location = txt[pos:pos + 80].strip()

        if title:
            items.append(
                {
                    "url": url,
                    "title": title,
                    "price_value": price,
                    "location": location,
                }
            )

    # дедуп по url
    seen = set()
    out = []
    for it in items:
        if it["url"] in seen:
            continue
        seen.add(it["url"])
        out.append(it)
    return out


def fetch_olx_pages(start_url: str, max_pages: int) -> List[str]:
    pages = []
    url = start_url

    headers = {"User-Agent": settings.OLX_USER_AGENT, "Accept-Language": "pl-PL,pl;q=0.9,en;q=0.8"}

    with httpx.Client(timeout=25.0, headers=headers, follow_redirects=True) as client:
        for page in range(1, max_pages + 1):
            r = client.get(url)
            if r.status_code in (403, 429):
                raise RuntimeError(f"OLX blocked: HTTP {r.status_code}")
            r.raise_for_status()
            pages.append(r.text)

            # сторінки: ?page=2
            if page == 1:
                joiner = "&" if "?" in start_url else "?"
            url = f"{start_url}{joiner}page={page+1}"

    return pages


def scrape_listings(start_url: str, max_pages: int) -> List[Dict]:
    html_pages = fetch_olx_pages(start_url, max_pages=max_pages)
    all_items: List[Dict] = []
    for html in html_pages:
        all_items.extend(_extract_listings(html))
    # дедуп по url
    seen = set()
    out = []
    for it in all_items:
        if it["url"] in seen:
            continue
        seen.add(it["url"])
        out.append(it)
    return out
