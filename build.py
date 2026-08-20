#!/usr/bin/env python3
"""Regenerate the publication list from INSPIRE-HEP.

    python3 build.py            # fetch, write publications.html, refresh index.html
    python3 build.py --offline  # rebuild from the cached data/publications.json

The list is fetched once and cached, so the site can be rebuilt without network.
Papers I led or co-led are flagged from LEAD_IDS below -- INSPIRE cannot know that,
so it is the one thing kept by hand. Add an arXiv id there when a new one lands.
"""
import argparse
import html
import json
import re
import urllib.request
from pathlib import Path

INSPIRE_RECID = 1888974
API = (f"https://inspirehep.net/api/literature?q=authors.recid%3A{INSPIRE_RECID}"
       "&size=300&sort=mostrecent"
       "&fields=titles,arxiv_eprints,publication_info,earliest_date,document_type,authors")

LEAD_IDS = {
    "2004.01448", "2012.04008", "2203.07886", "2203.11045", "2306.06311", "2306.06316",
    "2310.09116", "2405.03447", "2407.04473", "2412.06892", "2501.16852", "2505.09493",
    "2507.00157", "2509.13593", "2601.11139", "2601.21432", "2602.03382", "2604.09407",
}

# Typos in the upstream INSPIRE records. Reported there; corrected here meanwhile.
TITLE_FIXES = {
    "ZTF type Iasupernovae": "ZTF type Ia supernovae",
}

ROOT = Path(__file__).parent
CACHE = ROOT / "data" / "publications.json"
N_RECENT = 6


def fetch(offline=False):
    if offline or CACHE.exists() and offline:
        return json.loads(CACHE.read_text())
    with urllib.request.urlopen(API, timeout=60) as r:
        data = json.load(r)
    CACHE.parent.mkdir(exist_ok=True)
    CACHE.write_text(json.dumps(data, indent=1))
    return data


def tex_to_html(s):
    """INSPIRE titles carry TeX fragments; render the few that actually occur."""
    s = re.sub(r"\$?\\?alpha\$?", "α", s)
    s = re.sub(r"\$\\?beta\$", "β", s)
    s = re.sub(r"\$\\?sigma_?8?\$", "σ₈", s)
    s = s.replace("$", "").replace("\\", "")
    for wrong, right in TITLE_FIXES.items():
        s = s.replace(wrong, right)
    return html.escape(" ".join(s.split()))


def journal(rec):
    pub = (rec.get("publication_info") or [{}])[0]
    title = pub.get("journal_title")
    if not title:
        return "preprint"
    bits = [title]
    if pub.get("journal_volume"):
        bits.append(pub["journal_volume"])
    page = pub.get("artid") or pub.get("page_start")
    if page:
        bits.append(str(page))
    return " ".join(bits)


def parse(data):
    out = []
    for hit in data["hits"]["hits"]:
        m = hit["metadata"]
        if "thesis" in (m.get("document_type") or []):
            continue
        eid = (m.get("arxiv_eprints") or [{}])[0].get("value", "")
        authors = m.get("authors") or []
        out.append(dict(
            year=(m.get("earliest_date") or "")[:4],
            title=tex_to_html(m["titles"][0]["title"]),
            arxiv=eid,
            journal=journal(m),
            n_authors=len(authors),
            first=(authors[0]["full_name"].split(",")[0] if authors else ""),
            lead=eid in LEAD_IDS,
        ))
    return out


def entry_html(p):
    link = f"https://arxiv.org/abs/{p['arxiv']}" if p["arxiv"] else "#"
    meta = p["journal"]
    if p["n_authors"] > 12:
        meta += f" · {p['first']} et al. ({p['n_authors']} authors)"
    elif p["first"]:
        meta += f" · {p['first']} et al."
    if p["arxiv"]:
        meta += f" · arXiv:{p['arxiv']}"
    return (f'    <li class="pub{" pub--lead" if p["lead"] else ""}">\n'
            f'      <span class="pub__year">{p["year"]}</span>\n'
            f'      <span><a class="pub__title" href="{link}">{p["title"]}</a>\n'
            f'        <span class="pub__meta">{html.escape(meta)}</span></span>\n'
            f'    </li>')


def write_publications(pubs):
    lead = sum(p["lead"] for p in pubs)
    body = "\n".join(entry_html(p) for p in pubs)
    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Publications — Corentin Ravoux</title>
<meta name="description" content="Publication list of Corentin Ravoux, CNRS researcher at LPCA.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,300;0,6..72,400;1,6..72,400&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@300;400;500&display=swap" rel="stylesheet">
<link rel="canonical" href="https://corentinravoux.github.io/publications.html">
<meta property="og:type" content="website">
<meta property="og:title" content="Publications — Corentin Ravoux">
<meta property="og:description" content="Full publication list of Corentin Ravoux, CNRS researcher at LPCA, generated from INSPIRE-HEP.">
<meta property="og:url" content="https://corentinravoux.github.io/publications.html">
<meta property="og:image" content="https://corentinravoux.github.io/assets/img/cosmic-web.jpg">
<meta property="og:site_name" content="Corentin Ravoux">
<meta name="twitter:card" content="summary_large_image">
<meta name="author" content="Corentin Ravoux">
<link rel="stylesheet" href="assets/css/site.css">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'><circle cx='16' cy='16' r='9' fill='none' stroke='%2386e0b4' stroke-width='2'/><circle cx='16' cy='16' r='2' fill='%23f77f00'/></svg>">
</head>
<body>
<main class="page" style="margin-left:0">
  <section>
    <div class="wrap">
      <div class="eyebrow">Publications</div>
      <h2>{len(pubs)} papers</h2>
      <p>{lead} led or co-led, marked <span style="color:var(--signal)">●</span>. Generated from
        INSPIRE-HEP; run <code>python3 build.py</code> to refresh.</p>
      <div class="actions">
        <a class="btn" href="index.html">← Home</a>
        <a class="btn" href="https://inspirehep.net/authors/{INSPIRE_RECID}">INSPIRE-HEP</a>
        <a class="btn" href="https://scholar.google.com/citations?user=qcvRqBAAAAAJ">Google Scholar</a>
      </div>
      <ul class="pubs">
{body}
      </ul>
    </div>
  </section>
</main>
</body>
</html>
"""
    (ROOT / "publications.html").write_text(page)


def refresh_index(pubs):
    index = ROOT / "index.html"
    text = index.read_text()
    recent = "\n".join(entry_html(p) for p in pubs[:N_RECENT])
    block = f'<!-- RECENT-PUBS -->\n      <ul class="pubs">\n{recent}\n      </ul>\n      <!-- /RECENT-PUBS -->'
    if "<!-- /RECENT-PUBS -->" in text:
        text = re.sub(r"<!-- RECENT-PUBS -->.*?<!-- /RECENT-PUBS -->", block, text, flags=re.S)
    else:
        text = text.replace("<!-- RECENT-PUBS -->", block)
    index.write_text(text)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--offline", action="store_true", help="use data/publications.json")
    args = ap.parse_args()

    raw = json.loads(CACHE.read_text()) if args.offline else fetch()
    pubs = parse(raw)
    write_publications(pubs)
    refresh_index(pubs)
    print(f"{len(pubs)} publications ({sum(p['lead'] for p in pubs)} lead) "
          f"-> publications.html, index.html refreshed")
